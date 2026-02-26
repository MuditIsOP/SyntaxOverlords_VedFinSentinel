import hashlib
import time
from app.services.behavioral import fetch_recent_user_transactions
import json
import uuid
from typing import Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta, timezone
import structlog
from fastapi import Request

from app.schemas.predict import TransactionRequest, FraudScoreResponse
from app.models.transaction import Transaction
from app.models.risk_audit_log import RiskAuditLog
from app.models.base import RiskBandEnum, ActionTakenEnum
from app.models.user import User

from app.ml.models.ensemble import ensemble
from app.ml.explainer.explainer import explainer
from app.ml.vedic.anurupyena import compute_anurupyena_checksum, verify_transaction_integrity
from app.ml.vedic.nikhilam import nikhilam_threshold, benchmark_nikhilam_vs_standard
from app.services.behavioral import aggregate_features
from app.services.baseline_service import update_user_baseline

logger = structlog.get_logger()

# Baseline auto-update interval: recompute every N transactions
BASELINE_UPDATE_INTERVAL = 10


async def _compute_velocity_features(session: AsyncSession, user_id, current_timestamp: datetime) -> dict:
    """
    Compute REAL velocity features by counting actual recent transactions.
    Returns velocity_1h and velocity_24h as normalized counts (0-1 scale).
    """
    ts_aware = current_timestamp
    if ts_aware.tzinfo is None:
        ts_aware = ts_aware.replace(tzinfo=timezone.utc)

    window_1h = ts_aware - timedelta(hours=1)
    window_24h = ts_aware - timedelta(hours=24)

    # Count transactions in 1h window
    count_1h_q = select(func.count(Transaction.txn_id)).where(
        Transaction.user_id == user_id,
        Transaction.txn_timestamp >= window_1h
    )
    res_1h = await session.execute(count_1h_q)
    count_1h = res_1h.scalar() or 0

    # Count transactions in 24h window
    count_24h_q = select(func.count(Transaction.txn_id)).where(
        Transaction.user_id == user_id,
        Transaction.txn_timestamp >= window_24h
    )
    res_24h = await session.execute(count_24h_q)
    count_24h = res_24h.scalar() or 0

    # Normalize to 0-1: 50 txns/hour or 200 txns/day = 1.0
    return {
        "velocity_1h": min(1.0, count_1h / 50.0),
        "velocity_24h": min(1.0, count_24h / 200.0),
    }


async def process_fraud_prediction(
    request: Request,
    payload: TransactionRequest,
    session: AsyncSession
) -> FraudScoreResponse:
    """
    Core pipeline orchestrating Vedic computations, Behavioral ML aggregation,
    Ensemble Inference, and strictly immutable Risk Audit Logging.
    """
    start_time = time.perf_counter_ns()

    # 1. Fetch User baseline
    user = await session.get(User, payload.user_id)
    baseline = user.baseline_stats if user else {}
    base_risk = user.risk_profile.name if user else "UNKNOWN"

    risk_multipliers = {"LOW": 1.0, "MEDIUM": 1.5, "HIGH": 2.0, "BLACKLISTED": 5.0, "UNKNOWN": 1.5}
    r_factor = risk_multipliers.get(base_risk, 1.5)

    # 2. Vedic Pre-Filter: Compute AND verify Anurupyena checksum
    val_checksum = compute_anurupyena_checksum(
        amount=payload.amount,
        timestamp_iso=payload.txn_timestamp.isoformat(),
        geo_lat=payload.geo_lat,
        geo_lng=payload.geo_lng
    )

    # Verify vedic checksum if client provided one (tamper detection)
    vedic_checksum_valid = True
    vedic_integrity_failed = False
    if hasattr(payload, 'vedic_checksum') and payload.vedic_checksum:
        vedic_checksum_valid = verify_transaction_integrity(
            payload.vedic_checksum, payload.amount,
            payload.txn_timestamp.isoformat(),
            payload.geo_lat, payload.geo_lng
        )
        if not vedic_checksum_valid:
            vedic_integrity_failed = True
            logger.warning("vedic_checksum_mismatch",
                           received=payload.vedic_checksum,
                           computed=val_checksum)

    # Structural anomaly check (zero-coordinate high-value injection)
    vedic_anomaly = (payload.geo_lat == 0.0 and payload.geo_lng == 0.0 and payload.amount > 9000)
    if vedic_anomaly or vedic_integrity_failed:
        logger.warning("vedic_prefilter_blocked", checksum=val_checksum,
                       integrity_failed=vedic_integrity_failed)

        latency_ms = int((time.perf_counter_ns() - start_time) / 1_000_000)

        txn_db = Transaction(**payload.model_dump())
        txn_db.fraud_label = True
        txn_db.vedic_checksum = val_checksum
        txn_db.vedic_valid = False
        session.add(txn_db)
        await session.flush()

        block_reason = ("Vedic Pre-filter: structural anomaly detected (zero-coordinate high-value injection)"
                        if vedic_anomaly else
                        "Vedic Pre-filter: Anurupyena checksum mismatch — potential payload tampering")

        log_payload = f"{payload.user_id}:1.0:0.0:BLOCKED:{payload.txn_timestamp}"
        log_hash = hashlib.sha256(log_payload.encode()).hexdigest()
        audit_log = RiskAuditLog(
            txn_id=txn_db.txn_id,
            fraud_score=1.0,
            risk_band=RiskBandEnum.FRAUD,
            index_scores={"vedic_anomaly": 1.0},
            shap_values={"vedic_prefilter": "blocked"},
            human_explanation=block_reason,
            nikhilam_threshold=0.0,
            xgboost_score=0.0,
            isolation_score=0.0,
            action_taken=ActionTakenEnum.BLOCKED,
            log_hash=log_hash,
            latency_ms=latency_ms
        )
        session.add(audit_log)
        await session.commit()

        return FraudScoreResponse(
            txn_id=txn_db.txn_id,
            fraud_score=1.0,
            risk_band=RiskBandEnum.FRAUD.name,
            action_taken=ActionTakenEnum.BLOCKED.name,
            reasons=[block_reason],
            latency_ms=latency_ms,
            nikhilam_speedup=1.0,
            vedic_checksum_valid=False
        )

    # 3. Behavioral Feature Generation
    txn_dict = payload.model_dump()
    behavioral_features = await aggregate_features(session, txn_dict, baseline)

    # 4. Compute REAL velocity features from DB (not placeholder amounts)
    velocity = await _compute_velocity_features(session, payload.user_id, payload.txn_timestamp)

    # Issue #10: Compute real behavioral features (EWMA deviation, behavioral drift)
    ewma_deviation = 0.0
    behavioral_drift = 0.0
    if baseline:
        amt_mean = baseline.get("amount_mean", 0)
        amt_std = baseline.get("amount_std", 1)
        if amt_mean > 0:
            ewma_deviation = min(1.0, abs(payload.amount - amt_mean) / max(amt_mean, 1) / 3.0)
        # Drift: compare recent avg to old baseline (use baseline as old)
        if recent_txns := await fetch_recent_user_transactions(session, payload.user_id, limit=5):
            recent_mean = float(sum(float(t.amount) for t in recent_txns) / len(recent_txns))
            old_mean = amt_mean if amt_mean > 0 else recent_mean
            behavioral_drift = min(1.0, abs(recent_mean - old_mean) / max(old_mean, 1))

    # Build ML input vector
    ml_inputs = {
        "amount": payload.amount,
        "is_weekend": 1 if payload.txn_timestamp.weekday() >= 5 else 0,
        "hour_of_day": payload.txn_timestamp.hour,
        "account_age_days": user.account_age_days if user else 0,
        **behavioral_features,
        "device_trust_score": behavioral_features.get("DTS", 0.5),
        # Issue #6: ip_risk_score REMOVED — model retrained without it
        "merchant_risk_score": behavioral_features.get("MRS", 0.5),
        "beneficiary_risk_score": behavioral_features.get("BDS", 0.0),
        "velocity_1h": velocity["velocity_1h"],
        "velocity_24h": velocity["velocity_24h"],
        "geo_velocity_kmh": behavioral_features.get("SGAS", 0.0),
        "anurupyena_conflict": 1.0 if vedic_integrity_failed else 0.0,
        # Issue #10: Real behavioral features
        "ewma_deviation": ewma_deviation,
        "behavioral_drift": behavioral_drift,
    }

    # Issue #2 FIX: Compute proxy values for frequency/V-features from user history
    # instead of hardcoding to constants. Uses baseline stats + training population medians.
    # At training, card1 = user proxy. At runtime, user_id serves same role via baseline_stats.
    _user_txn_count = (user.total_txn_count or 1) if user else 1
    _freq_proxy = min(1.0, 1.0 / max(_user_txn_count, 1))  # Rare user = low freq
    _medians = ensemble._feature_medians or {}  # Training population medians

    ml_inputs.update({
        "card1_freq": max(0.001, _medians.get("card1_freq", _freq_proxy)),
        "card2_freq": max(0.001, _medians.get("card2_freq", _freq_proxy)),
        "addr1_freq": max(0.001, _medians.get("addr1_freq", _freq_proxy)),
        "email_freq": max(0.001, _medians.get("email_freq", _freq_proxy)),
        "card1_amt_mean": (baseline.get("amount_mean", 5000) / 50000.0) if baseline else _medians.get("card1_amt_mean", 0.1),
        "card1_amt_std": (baseline.get("amount_std", 1500) / 20000.0) if baseline else _medians.get("card1_amt_std", 0.075),
        # V-feature aggregates — use training population medians instead of 0
        "V_group1_mean": _medians.get("V_group1_mean", 0.0),
        "V_group2_mean": _medians.get("V_group2_mean", 0.0),
        "V_group3_mean": _medians.get("V_group3_mean", 0.0),
        "V_group4_mean": _medians.get("V_group4_mean", 0.0),
        "V258": _medians.get("V258", 0.0),
        "V283": _medians.get("V283", 0.0),
        "V294": _medians.get("V294", 0.0),
        "V306": _medians.get("V306", 0.0),
        "V307": _medians.get("V307", 0.0),
        "V310": _medians.get("V310", 0.0),
        "V312": _medians.get("V312", 0.0),
        "V313": _medians.get("V313", 0.0),
    })

    # 5. Sentinel Ensemble Inference
    xgb_prob, iso_score, feature_array = ensemble.predict(ml_inputs)

    # 6. Vedic Calibration (Nikhilam) & Explainability
    vedic_benchmark = benchmark_nikhilam_vs_standard(score=xgb_prob, risk_factor=r_factor)
    speedup = vedic_benchmark["speedup_multiplier"]

    # Nikhilam-computed dynamic threshold — ACTUALLY used for risk banding
    nik_thresh = nikhilam_threshold(score=xgb_prob, risk_factor=r_factor)

    # Human Explanations
    explanations = explainer.generate_explanations(feature_array, top_k=3)

    # 7. Risk Banding — Uses Nikhilam threshold + combined score
    behavioral_avg = sum(
        behavioral_features.get(k, 0) for k in
        ["ADI", "GRI", "DTS", "MRS", "BFI", "BDS", "VRI", "SGAS"]
    ) / 8.0
    combined_score = (xgb_prob * 0.5) + (behavioral_avg * 0.3) + (iso_score * 0.2 if iso_score > 0 else 0)

    # The Nikhilam threshold adjusts sensitivity per-user:
    # Higher risk_factor → lower nik_thresh → more sensitive detection
    fraud_threshold = min(0.65, nik_thresh * 0.8)
    suspicious_threshold = min(0.40, nik_thresh * 0.5)
    monitor_threshold = min(0.25, nik_thresh * 0.3)

    # Issue #9: Removed arbitrary iso_score > 0.8 hard cutoff
    if combined_score >= fraud_threshold or xgb_prob >= 0.75:
        band = RiskBandEnum.FRAUD
        action = ActionTakenEnum.BLOCKED
    elif combined_score >= suspicious_threshold or xgb_prob >= 0.50:
        band = RiskBandEnum.SUSPICIOUS
        action = ActionTakenEnum.HELD
    elif combined_score >= monitor_threshold:
        band = RiskBandEnum.MONITOR
        action = ActionTakenEnum.HELD
    else:
        band = RiskBandEnum.SAFE
        action = ActionTakenEnum.APPROVED

    latency_ms = int((time.perf_counter_ns() - start_time) / 1_000_000)

    # 8. Immutable Audit Logging
    log_payload_str = f"{payload.user_id}:{xgb_prob}:{iso_score}:{action}:{payload.txn_timestamp}"
    log_hash = hashlib.sha256(log_payload_str.encode()).hexdigest()

    txn_db = Transaction(**payload.model_dump())
    txn_db.fraud_label = (band == RiskBandEnum.FRAUD)
    txn_db.vedic_checksum = val_checksum
    txn_db.vedic_valid = vedic_checksum_valid
    session.add(txn_db)
    await session.flush()

    audit_log = RiskAuditLog(
        txn_id=txn_db.txn_id,
        fraud_score=xgb_prob,
        risk_band=band,
        index_scores=behavioral_features,
        shap_values={"raw_impact": explanations},
        human_explanation=" | ".join(explanations),
        nikhilam_threshold=nik_thresh,
        xgboost_score=xgb_prob,
        isolation_score=iso_score,
        action_taken=action,
        log_hash=log_hash,
        latency_ms=latency_ms
    )
    session.add(audit_log)
    await session.commit()

    # 9. Baseline Auto-Update: recompute every N transactions
    if user:
        txn_count = (user.total_txn_count or 0) + 1
        user.total_txn_count = txn_count
        if txn_count % BASELINE_UPDATE_INTERVAL == 0:
            try:
                await update_user_baseline(session, payload.user_id)
                logger.info("baseline_auto_updated", user_id=str(payload.user_id),
                            txn_count=txn_count)
            except Exception as e:
                logger.warning("baseline_auto_update_failed", error=str(e))
        await session.commit()

    logger.info("prediction_audit_saved",
                txn_id=str(txn_db.txn_id),
                action=action,
                latency=latency_ms)

    # 10. Dispatch Response
    return FraudScoreResponse(
        txn_id=txn_db.txn_id,
        fraud_score=xgb_prob,
        risk_band=band.name,
        action_taken=action.name,
        reasons=explanations,
        latency_ms=latency_ms,
        nikhilam_speedup=speedup,
        vedic_checksum_valid=vedic_checksum_valid
    )
