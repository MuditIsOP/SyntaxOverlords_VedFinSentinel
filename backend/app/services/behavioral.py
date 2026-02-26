from datetime import datetime, timezone
from math import radians, cos, sin, asin, sqrt
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from app.models.transaction import Transaction
from app.models.risk_audit_log import RiskAuditLog
from app.models.base import RiskBandEnum

# --- Helper Functions ---
def haversine(lon1, lat1, lon2, lat2):
    """Calculate the great circle distance between two points on the earth (specified in decimal degrees)"""
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers
    return c * r

def _ensure_tz(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

# --- Pure Logic Indices ---
def compute_adi(amount: float, user_baseline: dict) -> float:
    """Amount Deviation Index (ADI)"""
    mean = user_baseline.get("amount_mean", 0)
    std = user_baseline.get("amount_std", 1) # Prevent div 0
    if std == 0: 
        std = 1 
        if mean == 0: return 0.0 # Brand new user
    
    z_score = abs(amount - mean) / std
    return min(1.0, z_score / 3.0)

def compute_gri(lat: Optional[float], lng: Optional[float], user_baseline: dict) -> float:
    """Geographic Risk Index (GRI)"""
    if lat is None or lng is None: return 0.5 # Unknown location is medium risk
    
    trusted_locations = user_baseline.get("trusted_locations", [])
    if not trusted_locations: return 0.7 # No trusted history
    
    min_dist = float('inf')
    for loc in trusted_locations:
        # Assuming loc looks like {"lat": 12.0, "lng": 77.0}
        dist = haversine(lng, lat, loc.get("lng"), loc.get("lat"))
        if dist < min_dist:
            min_dist = dist
            
    # Scale: 0km = 0.0 risk, 500km+ = 1.0 risk
    return min(1.0, min_dist / 500.0)

def compute_dts(device_id: str, user_baseline: dict) -> float:
    """Device Trust Score (DTS) — Gradual trust based on device usage frequency."""
    trusted_devices = user_baseline.get("trusted_devices", [])
    device_counts = user_baseline.get("device_counts", {})
    
    if device_id not in trusted_devices:
        return 1.0  # Never-seen device = maximum risk
    
    # Gradual trust: more uses = more trusted
    count = device_counts.get(device_id, 1)
    if count >= 5:
        return 0.0   # Fully trusted
    elif count >= 3:
        return 0.15
    elif count >= 2:
        return 0.3
    else:
        return 0.6   # Seen once = still risky

def compute_trc(txn_timestamp: datetime, user_baseline: dict) -> float:
    """Time-based Risk Coefficient (TRC) — Continuous distance from active hours."""
    active_hours = user_baseline.get("active_hours", list(range(8, 23)))
    hour = txn_timestamp.hour
    
    if not active_hours or hour in active_hours:
        return 0.0
    
    # Calculate minimum circular distance to any active hour
    min_dist = min(min(abs(hour - h), 24 - abs(hour - h)) for h in active_hours)
    
    # Scale: 1 hour away = 0.15, 3 hours = 0.5, 6+ hours = 1.0
    return min(1.0, min_dist / 6.0)

def compute_mrs(merchant_category: str, user_baseline: dict) -> float:
    """Merchant Risk Score (MRS)"""
    # Expanded High risk categories based on standard FinTech risk profiles
    high_risk_cats = ["CRYPTO", "GAMBLING", "ADULT", "WIRE_TRANSFER", "PRECIOUS_METALS", "GIFT_CARDS", "LUXURY_GOODS"]
    if merchant_category.upper() in high_risk_cats:
        return 0.95 # Near-certain alert for sensitive categories
    
    # Suspicious categories (higher than baseline)
    suspicious_cats = ["LIQUOR", "ELECTRONICS", "TELECOM_SERVICES"]
    if merchant_category.upper() in suspicious_cats:
        return 0.6
    
    frequent_cats = user_baseline.get("frequent_merchant_categories", [])
    if merchant_category in frequent_cats:
        return 0.0
    
    return 0.3 # Default baseline for unknown but not globally blacklisted

# --- DB Coupled Indices ---
async def fetch_recent_user_transactions(session: AsyncSession, user_id, limit=10) -> List[Transaction]:
    stmt = select(Transaction).filter_by(user_id=user_id).order_by(desc(Transaction.txn_timestamp)).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())

def compute_bfi(recent_txns: List[Transaction], current_timestamp: datetime) -> float:
    """Burst Frequency Indicator (BFI) - PRD 6.265"""
    if len(recent_txns) < 3: return 0.0
    
    # Check time diff between current and the 3rd most recent
    time_diff_seconds = (_ensure_tz(current_timestamp) - _ensure_tz(recent_txns[2].txn_timestamp)).total_seconds()
    
    # Scale: < 60s = 1.0 (Critical), < 300s = 0.5 (Warn), > 1800s = 0.0 (Normal)
    if time_diff_seconds < 60:
        return 1.0
    elif time_diff_seconds < 300:
        return 0.6
    elif time_diff_seconds < 1800:
        return 0.2
    return 0.0

async def compute_bds(session: AsyncSession, recipient_id: Optional[str]) -> float:
    """Beneficiary Danger Score (BDS) - PRD 6.266
    
    Scores recipients based on their actual fraud history in the database.
    - Queries how many times this recipient received funds in flagged transactions
    - Score = flagged_count / total_received_count, capped at 1.0
    - Unknown recipients (zero history) get 0.3 (moderate risk, not zero)
    """
    if not recipient_id:
        return 0.0
    
    # Count total transactions received by this recipient
    total_query = select(func.count(Transaction.txn_id)).where(
        Transaction.recipient_id == recipient_id
    )
    total_res = await session.execute(total_query)
    total_received = total_res.scalar() or 0
    
    if total_received == 0:
        return 0.3  # Unknown recipient = moderate risk (not zero)
    
    # Count flagged transactions (FRAUD or SUSPICIOUS) involving this recipient
    flagged_query = select(func.count(Transaction.txn_id)).join(
        RiskAuditLog, Transaction.txn_id == RiskAuditLog.txn_id
    ).where(
        Transaction.recipient_id == recipient_id,
        RiskAuditLog.risk_band.in_([RiskBandEnum.FRAUD, RiskBandEnum.SUSPICIOUS])
    )
    flagged_res = await session.execute(flagged_query)
    flagged_count = flagged_res.scalar() or 0
    
    return min(1.0, flagged_count / total_received)

def compute_vri(recent_txns: List[Transaction], current_device: str) -> float:
    """Velocity Risk Index (VRI) — Time-decayed device switch score."""
    if not recent_txns: return 0.0
    
    last_txn = recent_txns[0]
    time_diff = (datetime.now(timezone.utc) - _ensure_tz(last_txn.txn_timestamp)).total_seconds()
    
    if current_device == last_txn.device_id:
        return 0.0  # Same device, no switch
    
    # Exponential decay: switch within seconds = 0.95, 30min = ~0.37, 1hr = ~0.14, 2hr+ ≈ 0
    import math
    decay_score = 0.95 * math.exp(-time_diff / 1800.0)  # τ = 30 minutes
    return round(min(1.0, decay_score), 4)
    
def compute_sgas(recent_txns: List[Transaction], current_lat: float, current_lng: float) -> float:
    """Simultaneous Geo-Anomaly Score (SGAS) — Continuous implied-speed score."""
    if not recent_txns or current_lat is None or current_lng is None: return 0.0
    
    last_txn = recent_txns[0]
    if last_txn.geo_lat is None or last_txn.geo_lng is None: return 0.0
    
    dist_km = haversine(current_lng, current_lat, float(last_txn.geo_lng), float(last_txn.geo_lat))
    time_diff_hours = (datetime.now(timezone.utc) - _ensure_tz(last_txn.txn_timestamp)).total_seconds() / 3600.0
    
    if time_diff_hours == 0:
        return 1.0 if dist_km > 1 else 0.0  # Instantaneous teleport
    
    implied_speed_kmh = dist_km / time_diff_hours
    
    # Continuous scale: 0 km/h = 0.0, 500 km/h = 0.5, 1000+ km/h = 1.0
    return round(min(1.0, implied_speed_kmh / 1000.0), 4)

# --- Issue #10 FIX: Sequence-based behavioral analysis ---
def compute_transaction_sequence_score(recent_txns: List[Transaction], current_amount: float,
                                        current_category: str) -> dict:
    """
    Analyze the SEQUENCE of recent transactions for temporal patterns.
    
    Unlike single-transaction heuristics, this examines the trajectory:
    - Amount escalation: monotonically increasing amounts suggest card testing
    - Time-gap acceleration: shorter gaps between transactions suggest automation
    - Category diversity: sudden shift to diverse/high-risk categories
    
    Returns: dict with sequence_escalation, sequence_acceleration, sequence_diversity scores (0-1)
    """
    if len(recent_txns) < 3:
        return {"sequence_escalation": 0.0, "sequence_acceleration": 0.0, "sequence_diversity": 0.0}
    
    # 1. Amount escalation: check if amounts are monotonically increasing
    amounts = [float(t.amount) for t in recent_txns[:5]] + [current_amount]
    increasing_pairs = sum(1 for i in range(len(amounts)-1) if amounts[i+1] > amounts[i])
    escalation = increasing_pairs / max(len(amounts) - 1, 1)
    
    # 2. Time-gap acceleration: are gaps getting shorter?
    timestamps = [_ensure_tz(t.txn_timestamp) for t in recent_txns[:5]]
    if len(timestamps) >= 3:
        gaps = [(timestamps[i] - timestamps[i+1]).total_seconds() for i in range(len(timestamps)-1)]
        # Gaps should be positive (recent first), check if decreasing
        if len(gaps) >= 2 and gaps[-1] > 0:
            acceleration_pairs = sum(1 for i in range(len(gaps)-1) if gaps[i+1] < gaps[i])
            acceleration = acceleration_pairs / max(len(gaps) - 1, 1)
        else:
            acceleration = 0.0
    else:
        acceleration = 0.0
    
    # 3. Category diversity in recent window
    categories = set(t.merchant_category for t in recent_txns[:5] if t.merchant_category)
    categories.add(current_category)
    high_risk_cats = {"CRYPTO", "GAMBLING", "ADULT", "WIRE_TRANSFER", "PRECIOUS_METALS", "GIFT_CARDS"}
    high_risk_count = len(categories & high_risk_cats)
    diversity = min(1.0, (len(categories) / 5.0) * 0.5 + (high_risk_count / 3.0) * 0.5)
    
    return {
        "sequence_escalation": round(min(1.0, escalation), 4),
        "sequence_acceleration": round(min(1.0, acceleration), 4),
        "sequence_diversity": round(min(1.0, diversity), 4),
    }


async def aggregate_features(session: AsyncSession, txn_data: dict, user_baseline: dict) -> Dict[str, float]:
    """Orchestrates all 9 core indices + sequence-based features, asynchronously fetching db context when required."""
    
    # Gather DB context
    recent_txns = await fetch_recent_user_transactions(session, txn_data["user_id"])
    now = txn_data["txn_timestamp"]
    
    # Calculate all arrays
    features = {
        "ADI": compute_adi(txn_data["amount"], user_baseline),
        "GRI": compute_gri(txn_data.get("geo_lat"), txn_data.get("geo_lng"), user_baseline),
        "DTS": compute_dts(txn_data["device_id"], user_baseline),
        "TRC": compute_trc(now, user_baseline),
        "MRS": compute_mrs(txn_data["merchant_category"], user_baseline),
        "BFI": compute_bfi(recent_txns, now),
        "BDS": await compute_bds(session, txn_data.get("recipient_id")),
        "VRI": compute_vri(recent_txns, txn_data["device_id"]),
        "SGAS": compute_sgas(recent_txns, txn_data.get("geo_lat"), txn_data.get("geo_lng"))
    }
    
    # Issue #10 FIX: Add sequence-based behavioral analysis
    seq_scores = compute_transaction_sequence_score(
        recent_txns, txn_data["amount"], txn_data.get("merchant_category", "")
    )
    features.update(seq_scores)
    
    return features
