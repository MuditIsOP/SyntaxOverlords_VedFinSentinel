from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
import time
import uuid
import structlog
import os

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

# Scheduler instance (module-level so lifespan can manage it)
_scheduler = init_scheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    if not _scheduler.running:
        _scheduler.start()
    yield
    # Shutdown
    if _scheduler.running:
        _scheduler.shutdown()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        lifespan=lifespan,
    )

    # State attach limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # Custom Exception Handlers
    app.add_exception_handler(VedFinException, rfc7807_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)

    # CORS Middleware Setup - configurable via CORS_ORIGINS env var
    allowed_origins = settings.cors_origin_list
    if os.getenv("ENVIRONMENT") == "development":
        if "http://0.0.0.0:3000" not in allowed_origins:
            allowed_origins.append("http://0.0.0.0:3000")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
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
    @limiter.limit("10/minute")
    async def health_check(request: Request):
        """Health check endpoint with system status"""
        try:
            # Check database connection
            from sqlalchemy import text
            from app.db.session import engine
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            db_status = "healthy"
        except Exception as e:
            db_status = "unhealthy"
            logger.warning("health_check_db_failed", error=str(e))
            
        return {
            "status": "ok" if db_status == "healthy" else "degraded",
            "version": settings.VERSION,
            "environment": os.getenv("ENVIRONMENT", "development"),
            "database": db_status,
            "timestamp": time.time()
        }

    # API Routers
    from app.api.v1 import api_router
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app

app = create_app()
