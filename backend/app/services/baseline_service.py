"""
Baseline Service — Computes user behavioral baselines from transaction history.

Instead of relying on hardcoded seed data, this service queries a user's
actual transaction history (last 90 days) and computes:
- amount_mean, amount_std
- trusted_devices
- trusted_locations
- active_hours
- frequent_merchant_categories
"""
from datetime import datetime, timedelta, timezone
from collections import Counter
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.transaction import Transaction
from app.models.user import User
import structlog

logger = structlog.get_logger()

BASELINE_WINDOW_DAYS = 90
MIN_TRANSACTIONS_FOR_BASELINE = 3


async def compute_user_baseline(session: AsyncSession, user_id) -> dict:
    """
    Compute behavioral baseline for a user from their transaction history.
    
    Returns a dictionary suitable for storing in User.baseline_stats.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=BASELINE_WINDOW_DAYS)
    
    stmt = select(Transaction).where(
        Transaction.user_id == user_id,
        Transaction.txn_timestamp >= cutoff,
        Transaction.is_deleted == False
    ).order_by(Transaction.txn_timestamp.desc())
    
    result = await session.execute(stmt)
    txns = list(result.scalars().all())
    
    if len(txns) < MIN_TRANSACTIONS_FOR_BASELINE:
        # Not enough history — return sensible defaults
        return {
            "amount_mean": 5000.0,
            "amount_std": 3000.0,
            "trusted_devices": [],
            "trusted_locations": [],
            "active_hours": list(range(8, 23)),
            "frequent_merchant_categories": [],
            "baseline_txn_count": len(txns),
            "last_computed": datetime.now(timezone.utc).isoformat()
        }
    
    # --- Amount statistics ---
    amounts = [float(t.amount) for t in txns]
    amount_mean = sum(amounts) / len(amounts)
    amount_variance = sum((a - amount_mean) ** 2 for a in amounts) / len(amounts)
    amount_std = amount_variance ** 0.5
    
    # --- Trusted devices (seen 2+ times) ---
    device_counts = Counter(t.device_id for t in txns if t.device_id)
    trusted_devices = [dev for dev, count in device_counts.items() if count >= 2]
    
    # --- Trusted locations (cluster unique lat/lng seen 2+ times) ---
    loc_counter = Counter()
    for t in txns:
        if t.geo_lat is not None and t.geo_lng is not None:
            # Round to 2 decimal places for clustering (~1km precision)
            lat_r = round(float(t.geo_lat), 2)
            lng_r = round(float(t.geo_lng), 2)
            loc_counter[(lat_r, lng_r)] += 1
    
    trusted_locations = [
        {"lat": lat, "lng": lng}
        for (lat, lng), count in loc_counter.items() if count >= 2
    ]
    
    # --- Active hours (hours with any transaction) ---
    hour_counts = Counter(t.txn_timestamp.hour for t in txns)
    # Include hours that account for 90%+ of activity
    total_txn_count = sum(hour_counts.values())
    sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
    active_hours = []
    cumulative = 0
    for hour, count in sorted_hours:
        active_hours.append(hour)
        cumulative += count
        if cumulative >= total_txn_count * 0.9:
            break
    active_hours.sort()
    
    # --- Frequent merchant categories ---
    merchant_counts = Counter(t.merchant_category for t in txns if t.merchant_category)
    frequent_merchants = [cat for cat, count in merchant_counts.items() if count >= 2]
    
    baseline = {
        "amount_mean": round(amount_mean, 2),
        "amount_std": round(max(amount_std, 1.0), 2),  # Prevent div-by-zero
        "trusted_devices": trusted_devices[:20],  # Cap at 20
        "device_counts": {dev: count for dev, count in device_counts.most_common(20)},  # For gradual DTS
        "trusted_locations": trusted_locations[:10],  # Cap at 10
        "active_hours": active_hours,
        "frequent_merchant_categories": frequent_merchants,
        "baseline_txn_count": len(txns),
        "last_computed": datetime.now(timezone.utc).isoformat()
    }
    
    logger.info("baseline_computed", user_id=str(user_id), txn_count=len(txns))
    return baseline


async def update_user_baseline(session: AsyncSession, user_id) -> dict:
    """Compute and persist a user's baseline to the database."""
    baseline = await compute_user_baseline(session, user_id)
    
    user = await session.get(User, user_id)
    if user:
        user.baseline_stats = baseline
        await session.commit()
        logger.info("baseline_persisted", user_id=str(user_id))
    
    return baseline


async def update_all_baselines(session: AsyncSession):
    """Batch update baselines for all active users. Called by nightly scheduler."""
    stmt = select(User.user_id).where(User.is_deleted == False)
    result = await session.execute(stmt)
    user_ids = [row[0] for row in result.all()]
    
    updated = 0
    for uid in user_ids:
        try:
            await update_user_baseline(session, uid)
            updated += 1
        except Exception as e:
            logger.error("baseline_update_failed", user_id=str(uid), error=str(e))
    
    logger.info("batch_baseline_update_complete", updated=updated, total=len(user_ids))
    return updated
