from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import time
import random
from app.db.session import get_db_session

from app.services.metrics import compute_dashboard_metrics

router = APIRouter()

@router.get("/metrics", summary="Global Dashboard Metrics")
async def get_system_metrics(
    # token: VerifiedToken = Depends(),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Exposes high-level aggregates for the React Dashboard.
    In production, this heavily leverages Redis caching for speed.
    """
    
    return await compute_dashboard_metrics(db=db, window_hours=24)
