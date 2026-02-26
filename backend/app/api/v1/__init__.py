from fastapi import APIRouter
from app.api.v1.predict import router as predict_router
from app.api.v1.simulate import router as simulate_router
from app.api.v1.ws import router as ws_router
from app.api.v1.audit import router as audit_router
from app.api.v1.metrics import router as metrics_router
from app.api.v1.users import router as users_router
from app.api.v1.auth import router as auth_router

api_router = APIRouter()
api_router.include_router(predict_router, prefix="/scoring", tags=["Fraud Scoring"])
api_router.include_router(simulate_router, tags=["Simulation Engine"])
api_router.include_router(ws_router, tags=["Real-time Feeds"])
api_router.include_router(audit_router, tags=["Compliance & Audit"])
api_router.include_router(metrics_router, tags=["System Metrics"])
api_router.include_router(users_router, tags=["User Management"])
api_router.include_router(auth_router, prefix="/auth", tags=["System Security"])
