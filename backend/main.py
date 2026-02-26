from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import time
import uuid
import structlog

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import VedFinException, rfc7807_exception_handler, global_exception_handler
from app.core.scheduler import init_scheduler
from app.db.session import init_db

# Setup structlog
setup_logging()
logger = structlog.get_logger()

# Setup Rate Limiting
limiter = Limiter(key_func=get_remote_address)

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc"
    )

    # State attach limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # Custom Exception Handlers
    app.add_exception_handler(VedFinException, rfc7807_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)

    # CORS Middleware Setup
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://0.0.0.0:3000"
        ], 
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request ID & Timing Middleware
    @app.middleware("http")
    async def log_request_time_and_id(request: Request, call_next):
        start_time = time.perf_counter()
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        structlog.contextvars.bind_contextvars(request_id=request_id, path=request.url.path)
        
        response = await call_next(request)
        
        process_time_ms = int((time.perf_counter() - start_time) * 1000)
        response.headers["X-Process-Time"] = str(process_time_ms)
        response.headers["X-Request-ID"] = request_id
        
        logger.info(
            "request_completed",
            method=request.method,
            status_code=response.status_code,
            duration_ms=process_time_ms
        )
        return response

    # Health Check Example Route
    @app.get(f"{settings.API_V1_STR}/health")
    @limiter.limit("5/minute")
    async def health_check(request: Request):
        return {"status": "ok", "version": settings.VERSION}

    # API Routers
    from app.api.v1 import api_router
    app.include_router(api_router, prefix=settings.API_V1_STR)

    # Attach Scheduler
    app.state.scheduler = init_scheduler()
    
    @app.on_event("startup")
    async def startup_event():
        await init_db()
        if not app.state.scheduler.running:
            app.state.scheduler.start()
            
    @app.on_event("shutdown")
    async def shutdown_event():
        if app.state.scheduler.running:
            app.state.scheduler.shutdown()

    return app

app = create_app()
