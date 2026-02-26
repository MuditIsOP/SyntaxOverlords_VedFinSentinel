"""
Integration Tests — Real pipeline testing without mocking ML components.

Tests exercise the actual behavioral engine, baseline computation, and
fraud scoring pipeline with a test database.
"""
import asyncio
import sys
import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.models.base import Base, RiskProfileEnum, RiskBandEnum, ActionTakenEnum
from app.models.user import User
from app.models.transaction import Transaction
from app.models.risk_audit_log import RiskAuditLog


# Use in-memory SQLite for tests
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def db_session():
    """Create a fresh test database for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSession() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def _create_test_user(session: AsyncSession, txn_count: int = 20) -> tuple:
    """Helper: Create a user with transaction history."""
    user_id = uuid.uuid4()
    user = User(
        user_id=user_id,
        email=f"test_{user_id}@vedfin.com",
        hashed_password="$2b$12$test_hash_placeholder",
        risk_profile=RiskProfileEnum.MEDIUM,
        account_age_days=150,
        avg_txn_amount=5000.0,
        total_txn_count=txn_count,
        baseline_stats={}
    )
    session.add(user)
    
    # Create history transactions
    now = datetime.now(timezone.utc)
    for i in range(txn_count):
        txn = Transaction(
            txn_id=uuid.uuid4(),
            user_id=user_id,
            amount=3000 + (i * 100),  # ₹3000-₹5000 range
            txn_timestamp=now - timedelta(hours=i * 6),
            device_id="trusted_device_001",
            merchant_category="E-commerce" if i % 2 == 0 else "Food",
            geo_lat=28.6139,  # New Delhi
            geo_lng=77.2090,
            fraud_label=False
        )
        session.add(txn)
    
    await session.commit()
    return user_id, user


# ===== TEST 1: Baseline Computation =====
@pytest.mark.asyncio
async def test_compute_baseline_from_history(db_session):
    """Verify baseline is computed correctly from actual transaction history."""
    from app.services.baseline_service import compute_user_baseline
    
    user_id, _ = await _create_test_user(db_session, txn_count=20)
    baseline = await compute_user_baseline(db_session, user_id)
    
    # Amount stats should reflect the ₹3000-₹5000 range
    assert baseline["amount_mean"] > 2500
    assert baseline["amount_mean"] < 6000
    assert baseline["amount_std"] > 0  # Non-zero std
    assert baseline["baseline_txn_count"] == 20
    
    # Trusted devices should include our consistent device
    assert "trusted_device_001" in baseline["trusted_devices"]
    
    # Should have trusted locations near Delhi
    assert len(baseline["trusted_locations"]) >= 1
    
    # Should have activity hours
    assert len(baseline["active_hours"]) >= 1
    
    # Merchant categories should be detected
    assert "E-commerce" in baseline["frequent_merchant_categories"] or \
           "Food" in baseline["frequent_merchant_categories"]


# ===== TEST 2: Normal Transaction = Low Risk =====
@pytest.mark.asyncio
async def test_normal_transaction_low_risk(db_session):
    """Verify behavioral index functions return low scores for normal inputs."""
    from app.services.behavioral import compute_adi, compute_dts, compute_trc
    
    # Use a manually constructed baseline (known values, no DB dependency)
    baseline = {
        "amount_mean": 5000.0,
        "amount_std": 1500.0,
        "trusted_devices": ["trusted_device_001", "backup_device_002"],
        "device_counts": {"trusted_device_001": 10, "backup_device_002": 3},
        "trusted_locations": [{"lat": 28.61, "lng": 77.21}],
        "active_hours": [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21],
        "frequent_merchant_categories": ["E-commerce", "Food"]
    }
    
    # Normal amount: within 1 std of mean → ADI should be low
    adi = compute_adi(5000.0, baseline)  # Exactly at mean
    assert adi == 0.0, f"ADI should be 0 for exact mean amount, got {adi}"
    
    adi_close = compute_adi(6000.0, baseline)  # 0.67 std away
    assert adi_close < 0.3, f"ADI should be low for near-mean amount, got {adi_close}"
    
    # Known device
    dts = compute_dts("trusted_device_001", baseline)
    assert dts == 0.0, f"DTS should be 0 for trusted device, got {dts}"
    
    # Normal business hours
    normal_time = datetime(2026, 1, 15, 14, 30, 0, tzinfo=timezone.utc)
    trc = compute_trc(normal_time, baseline)
    assert trc <= 0.5, f"TRC should be low for business hours, got {trc}"


# ===== TEST 3: Anomalous Transaction = High Risk =====
@pytest.mark.asyncio
async def test_anomalous_transaction_high_risk(db_session):
    """Verify an anomalous transaction gets high risk scores."""
    from app.services.behavioral import compute_adi, compute_gri, compute_dts, compute_trc
    from app.services.baseline_service import compute_user_baseline
    
    user_id, _ = await _create_test_user(db_session, txn_count=15)
    baseline = await compute_user_baseline(db_session, user_id)
    
    # Large amount spike
    adi = compute_adi(50000.0, baseline)  # 10x the mean
    assert adi > 0.5, f"ADI should be high for 10x amount, got {adi}"
    
    # Different continent (London vs Delhi = ~6700km)
    gri = compute_gri(51.5074, -0.1278, baseline)
    assert gri > 0.5, f"GRI should be high for London, got {gri}"
    
    # New device
    dts = compute_dts("unknown_device_xyz", baseline)
    assert dts == 1.0, f"DTS should be 1.0 for unknown device, got {dts}"
    
    # 3 AM transaction
    odd_time = datetime(2026, 1, 15, 3, 0, 0, tzinfo=timezone.utc)
    trc = compute_trc(odd_time, baseline)
    # TRC depends on active_hours baseline — if 3AM not in active hours, should flag
    assert isinstance(trc, float)


# ===== TEST 4: BDS Recipient Scoring =====
@pytest.mark.asyncio
async def test_bds_recipient_scoring(db_session):
    """Verify BDS scores recipients based on actual flagged history."""
    from app.services.behavioral import compute_bds
    
    user_id = uuid.uuid4()
    bad_recipient = uuid.uuid4()
    
    # Create user
    user = User(
        user_id=user_id,
        email="bds_test@vedfin.com",
        hashed_password="$2b$12$test_hash",
        risk_profile=RiskProfileEnum.LOW,
        account_age_days=100
    )
    session = db_session
    session.add(user)
    
    # Create transactions TO the bad recipient (3 total, 2 flagged as FRAUD)
    for i in range(3):
        txn_id = uuid.uuid4()
        txn = Transaction(
            txn_id=txn_id,
            user_id=user_id,
            amount=10000,
            txn_timestamp=datetime.now(timezone.utc) - timedelta(hours=i),
            device_id="device",
            merchant_category="Wire Transfer",
            recipient_id=bad_recipient,
            fraud_label=i < 2  # First 2 are fraud
        )
        session.add(txn)
        
        if i < 2:  # Create audit log marking as FRAUD
            log = RiskAuditLog(
                log_id=uuid.uuid4(),
                txn_id=txn_id,
                fraud_score=0.95,
                risk_band=RiskBandEnum.FRAUD,
                index_scores={"adi": 0.8},
                shap_values={},
                human_explanation="Test",
                action_taken=ActionTakenEnum.FROZEN,
                log_hash="test_hash",
                latency_ms=50
            )
            session.add(log)
    
    await session.commit()
    
    # BDS should be ~0.67 (2 flagged out of 3 total)
    bds = await compute_bds(session, bad_recipient)
    assert 0.5 < bds <= 1.0, f"BDS should reflect flagged history, got {bds}"
    
    # Unknown recipient should get 0.3 (moderate risk)
    bds_unknown = await compute_bds(session, uuid.uuid4())
    assert bds_unknown == 0.3, f"Unknown recipient should get 0.3, got {bds_unknown}"


# ===== TEST 5: Cryptographic Integrity Check =====
@pytest.mark.asyncio
async def test_cryptographic_integrity():
    """Verify HMAC-SHA256 detects tampered payloads."""
    from app.ml.integrity import (
        compute_transaction_hash, verify_transaction_hash, detect_structural_anomaly
    )
    
    # Hash determinism
    h1 = compute_transaction_hash(
        5000.0, "2026-01-15T14:30:00+00:00", 
        "user-123", "device-456", 28.61, 77.21
    )
    h2 = compute_transaction_hash(
        5000.0, "2026-01-15T14:30:00+00:00", 
        "user-123", "device-456", 28.61, 77.21
    )
    assert h1 == h2, "Same inputs should produce same hash"
    
    # Tamper detection: changing amount changes hash
    h_tampered = compute_transaction_hash(
        5001.0, "2026-01-15T14:30:00+00:00", 
        "user-123", "device-456", 28.61, 77.21
    )
    assert h1 != h_tampered, "Different amount should produce different hash"
    
    # Verify integrity
    result = verify_transaction_hash(
        h1, 5000.0, "2026-01-15T14:30:00+00:00",
        "user-123", "device-456", 28.61, 77.21
    )
    assert result.valid == True
    
    # Tampered should fail
    result_tampered = verify_transaction_hash(
        h1, 6000.0, "2026-01-15T14:30:00+00:00",
        "user-123", "device-456", 28.61, 77.21
    )
    assert result_tampered.valid == False
    
    # Structural anomaly detection
    anomaly = detect_structural_anomaly(
        9500.0, 0.0, 0.0, "2026-01-15T14:30:00+00:00"
    )
    assert anomaly["should_block"] == True
    assert "zero_coordinate_high_value" in anomaly["anomalies"]


# ===== TEST 6: Statistical Behavioral Features =====
@pytest.mark.asyncio
async def test_statistical_behavioral_features():
    """Verify new statistical features work correctly."""
    from app.services.behavioral import (
        compute_amount_zscore, compute_velocity_entropy,
        compute_ewma_deviation, compute_time_of_day_anomaly
    )
    
    # Z-score calculation
    baseline = {"amount_mean": 1000.0, "amount_std": 200.0}
    zscore = compute_amount_zscore(1500.0, baseline)
    assert 0.0 <= zscore <= 1.0, f"Z-score should be in [0,1], got {zscore}"
    
    # Time anomaly
    from datetime import datetime, timezone
    tx_time = datetime(2026, 1, 15, 3, 0, 0, tzinfo=timezone.utc)  # 3 AM
    # Empty history should give moderate risk for unusual hour
    anomaly = compute_time_of_day_anomaly(tx_time, [])
    assert 0.0 <= anomaly <= 1.0


# ===== Issue #6 FIX: Feature Range and Model Tests =====

@pytest.mark.asyncio
async def test_feature_value_ranges(db_session):
    """Issue #6: Verify all 9 behavioral features return values in [0, 1] range."""
    from app.services.behavioral import aggregate_features
    from app.services.baseline_service import compute_user_baseline

    user_id, _ = await _create_test_user(db_session, txn_count=15)
    baseline = await compute_user_baseline(db_session, user_id)

    txn_data = {
        "user_id": user_id,
        "amount": 50000.0,
        "txn_timestamp": datetime(2026, 1, 15, 3, 0, 0, tzinfo=timezone.utc),
        "device_id": "unknown_device",
        "merchant_category": "CRYPTO",
        "geo_lat": 51.5,
        "geo_lng": -0.12,
        "recipient_id": uuid.uuid4(),
    }

    features = await aggregate_features(db_session, txn_data, baseline)

    for key, value in features.items():
        assert 0.0 <= value <= 1.0, f"Feature {key}={value} out of [0,1] range"


@pytest.mark.asyncio
async def test_model_loaded_and_predicts():
    """Issue #6: Verify model loads correctly and produces valid output."""
    from app.ml.models.ensemble import ensemble

    if not ensemble._is_loaded:
        try:
            ensemble.load_models()
        except Exception:
            pytest.skip("Model artifact not available")

    assert ensemble._feature_names is not None
    assert len(ensemble._feature_names) > 0

    # Create a dummy feature dict
    dummy = {f: 0.0 for f in ensemble._feature_names}
    dummy["amount"] = 5000.0
    dummy["hour_of_day"] = 14

    xgb_prob, iso_score, feat_arr = ensemble.predict(dummy)
    assert 0.0 <= xgb_prob <= 1.0, f"XGBoost prob out of range: {xgb_prob}"
    assert 0.0 <= iso_score <= 1.0, f"ISO score out of range: {iso_score}"

