from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any
import uuid

from app.models.user import User
from app.db.session import get_db_session

router = APIRouter()

@router.get("/users/{user_id}/baseline", summary="Get User Risk Baseline")
async def get_user_baseline(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieves the established behavioral baseline stats for a user."""
    user = await db.get(User, user_id)
    if not user:
        # Mocking fallback
        return {
            "user_id": user_id,
            "risk_profile": "MEDIUM",
            "baseline_stats": {
                "amount_mean": 500.0,
                "amount_std": 100.0,
                "trusted_devices": ["iphone-x"],
                "active_hours": [9,10,11,12,13,14,15,16,17]
            }
        }
    return {
        "user_id": user.user_id,
        "risk_profile": user.risk_profile.name,
        "baseline_stats": user.baseline_stats
    }

@router.post("/users/{user_id}/baseline/reset", summary="Reset User Risk Baseline")
async def reset_user_baseline(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Completely clear out user trusted metrics, forcing ML models to 
    re-learn or flag activity cautiously.
    """
    user = await db.get(User, user_id)
    if user:
        user.baseline_stats = {}
        user.trusted_devices = []
        user.trusted_locations = []
        user.avg_txn_amount = 0
        user.total_txn_count = 0
        await db.commit()
    
    return {"status": "success", "message": f"Baseline metrics explicitly cleared for user {user_id}"}
