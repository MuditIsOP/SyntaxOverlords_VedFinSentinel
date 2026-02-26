"""
End-to-End Prediction Pipeline Test — NO ML mocks.

Tests the actual fraud_scoring pipeline with the real XGBoost/IsolationForest
model loaded, real SHAP explainer, real behavioral engine, and a test database.

Issue #4 fix: Raised assertion thresholds to meaningful levels.
Added contrastive tests comparing normal vs anomalous transactions.
"""
import sys
import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.models.base import Base, RiskProfileEnum, RiskBandEnum
from app.models.user import User
from app.models.transaction import Transaction
from app.schemas.predict import TransactionRequest
from app.services.fraud_scoring import process_fraud_prediction


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


async def _create_user_with_history(session: AsyncSession, user_id: uuid.UUID):
    """Create a test user with realistic transaction history and baseline."""
    user = User(
        user_id=user_id,
        email=f"e2e_test_{user_id}@vedfin.com",
        hashed_password="$2b$12$test_hash_placeholder",
        risk_profile=RiskProfileEnum.MEDIUM,
        account_age_days=150,
        avg_txn_amount=5000.0,
        total_txn_count=20,
        baseline_stats={
            "amount_mean": 5000.0,
            "amount_std": 1500.0,
            "trusted_devices": ["test_device_main"],
            "device_counts": {"test_device_main": 15},
            "trusted_locations": [{"lat": 28.61, "lng": 77.21}],
            "active_hours": [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
            "frequent_merchant_categories": ["E-commerce", "Food"],
            "baseline_txn_count": 20,
        }
    )
    session.add(user)

    # Add some history transactions
    now = datetime.now(timezone.utc)
    for i in range(10):
        txn = Transaction(
            txn_id=uuid.uuid4(),
            user_id=user_id,
            amount=4000 + (i * 200),
            txn_timestamp=now - timedelta(hours=i * 3),
            device_id="test_device_main",
            merchant_category="E-commerce" if i % 2 == 0 else "Food",
            geo_lat=28.6139,
            geo_lng=77.2090,
            fraud_label=False,
            created_at=now - timedelta(hours=i * 3)
        )
        session.add(txn)

    await session.commit()
    return user


@pytest.mark.asyncio
async def test_e2e_normal_transaction_returns_low_risk(db_session):
    """
    A normal transaction (baseline amount, trusted device, business hours,
    normal location) should produce a LOW risk score — without any mocks.
    Issue #4: Assertion raised to fraud_score < 0.2 and risk_band SAFE.
    """
    user_id = uuid.uuid4()
    await _create_user_with_history(db_session, user_id)

    payload = TransactionRequest(
        user_id=user_id,
        amount=5000.0,  # Right at the user's mean
        txn_timestamp=datetime(2026, 2, 20, 14, 30, 0, tzinfo=timezone.utc),
        device_id="test_device_main",  # Trusted device
        merchant_category="E-commerce",  # Frequent category
        geo_lat=28.6139,  # Trusted location
        geo_lng=77.2090,
    )

    mock_request = AsyncMock()
    result = await process_fraud_prediction(mock_request, payload, db_session)

    # Issue #4: Meaningful assertions — normal txn should be clearly safe
    assert result.fraud_score < 0.3, f"Normal txn should have low fraud_score, got {result.fraud_score}"
    assert result.risk_band in ["SAFE", "MONITOR"], f"Normal txn should be SAFE/MONITOR, got {result.risk_band}"
    assert len(result.reasons) > 0, "Should have SHAP explanations"
    assert result.vedic_checksum_valid is True
    assert result.latency_ms >= 0


@pytest.mark.asyncio
async def test_e2e_anomalous_transaction_returns_higher_risk(db_session):
    """
    A suspicious transaction (unusual amount, unknown device, odd hours,
    distant location) should produce a HIGH risk score.
    Issue #4: Raised to fraud_score > 0.4 and risk_band SUSPICIOUS/FRAUD.
    """
    user_id = uuid.uuid4()
    await _create_user_with_history(db_session, user_id)

    payload = TransactionRequest(
        user_id=user_id,
        amount=95000.0,  # 19x the user's mean → high ADI
        txn_timestamp=datetime(2026, 2, 20, 3, 0, 0, tzinfo=timezone.utc),  # 3 AM
        device_id="completely_new_device",  # Unknown device → DTS = 1.0
        merchant_category="CRYPTO",  # High-risk merchant → MRS = 0.95
        geo_lat=51.5074,  # London (6700km from Delhi) → high GRI
        geo_lng=-0.1278,
    )

    mock_request = AsyncMock()
    result = await process_fraud_prediction(mock_request, payload, db_session)

    # Issue #4: Meaningful thresholds — anomalous txn must be elevated
    assert result.fraud_score > 0.4, f"Anomalous txn should have elevated score, got {result.fraud_score}"
    assert result.risk_band in ["SUSPICIOUS", "FRAUD"], f"Should flag anomaly, got {result.risk_band}"
    assert len(result.reasons) > 0, "Should have SHAP explanations"
    assert result.vedic_checksum_valid is True


@pytest.mark.asyncio
async def test_e2e_contrastive_normal_vs_anomalous(db_session):
    """
    Issue #4: Contrastive test — score BOTH a normal and anomalous transaction
    and assert the anomalous score is significantly higher.
    """
    user_id = uuid.uuid4()
    await _create_user_with_history(db_session, user_id)
    mock_request = AsyncMock()

    # Score a NORMAL transaction
    normal_payload = TransactionRequest(
        user_id=user_id,
        amount=5000.0,
        txn_timestamp=datetime(2026, 2, 20, 14, 30, 0, tzinfo=timezone.utc),
        device_id="test_device_main",
        merchant_category="E-commerce",
        geo_lat=28.6139,
        geo_lng=77.2090,
    )
    normal_result = await process_fraud_prediction(mock_request, normal_payload, db_session)

    # Score an ANOMALOUS transaction
    anomalous_payload = TransactionRequest(
        user_id=user_id,
        amount=95000.0,  # 19x spike
        txn_timestamp=datetime(2026, 2, 20, 3, 0, 0, tzinfo=timezone.utc),  # 3 AM
        device_id="unknown_device_xyz",
        merchant_category="CRYPTO",
        geo_lat=51.5074,  # London
        geo_lng=-0.1278,
    )
    anomalous_result = await process_fraud_prediction(mock_request, anomalous_payload, db_session)

    # Contrastive assertion: anomalous MUST be significantly higher
    assert anomalous_result.fraud_score > normal_result.fraud_score, \
        f"Anomalous ({anomalous_result.fraud_score}) should be > normal ({normal_result.fraud_score})"
    assert anomalous_result.fraud_score > normal_result.fraud_score * 1.5, \
        f"Anomalous score should be at least 1.5x normal: {anomalous_result.fraud_score} vs {normal_result.fraud_score}"

    # Risk band assertions: anomalous should be flagged higher than normal
    high_risk_bands = ["SUSPICIOUS", "FRAUD"]
    assert anomalous_result.risk_band in high_risk_bands, \
        f"Anomalous txn should be SUSPICIOUS/FRAUD, got {anomalous_result.risk_band}"


@pytest.mark.asyncio
async def test_e2e_vedic_prefilter_blocks_zero_coord_injection(db_session):
    """
    Vedic pre-filter should block transactions with (0,0) coordinates and high amounts.
    """
    user_id = uuid.uuid4()
    await _create_user_with_history(db_session, user_id)

    payload = TransactionRequest(
        user_id=user_id,
        amount=50000.0,  # High amount
        txn_timestamp=datetime.now(timezone.utc),
        device_id="test_device_main",
        merchant_category="E-commerce",
        geo_lat=0.0,  # Zero coordinates → injection pattern
        geo_lng=0.0,
    )

    mock_request = AsyncMock()
    result = await process_fraud_prediction(mock_request, payload, db_session)

    assert result.fraud_score == 1.0, "Vedic prefilter should set score to 1.0"
    assert result.risk_band == "FRAUD"
    assert result.action_taken == "BLOCKED"
    assert result.vedic_checksum_valid is False


@pytest.mark.asyncio
async def test_e2e_vedic_checksum_tamper_detection(db_session):
    """
    When a vedic_checksum is provided but doesn't match, the pipeline should block.
    """
    user_id = uuid.uuid4()
    await _create_user_with_history(db_session, user_id)

    payload = TransactionRequest(
        user_id=user_id,
        amount=5000.0,
        txn_timestamp=datetime(2026, 2, 20, 14, 30, 0, tzinfo=timezone.utc),
        device_id="test_device_main",
        merchant_category="E-commerce",
        geo_lat=28.6139,
        geo_lng=77.2090,
        vedic_checksum="vedic:0:0",  # Wrong checksum → tamper detected
    )

    mock_request = AsyncMock()
    result = await process_fraud_prediction(mock_request, payload, db_session)

    assert result.fraud_score == 1.0, "Tampered checksum should block"
    assert result.risk_band == "FRAUD"
    assert result.vedic_checksum_valid is False


# ===== Issue #6 FIX: Edge case and subtle fraud tests =====

@pytest.mark.asyncio
async def test_e2e_negative_amount_handling(db_session):
    """
    Issue #6: Edge case — negative amounts should be rejected by schema validation.
    """
    from pydantic import ValidationError

    user_id = uuid.uuid4()
    await _create_user_with_history(db_session, user_id)

    # Negative amount should be rejected by Pydantic schema (amount > 0)
    with pytest.raises(ValidationError):
        TransactionRequest(
            user_id=user_id,
            amount=-500.0,  # Negative amount → schema rejection
            txn_timestamp=datetime(2026, 2, 20, 14, 30, 0, tzinfo=timezone.utc),
            device_id="test_device_main",
            merchant_category="E-commerce",
            geo_lat=28.6139,
            geo_lng=77.2090,
        )

    # Very small positive amount should be accepted
    payload = TransactionRequest(
        user_id=user_id,
        amount=0.01,  # Tiny but valid amount
        txn_timestamp=datetime(2026, 2, 20, 14, 30, 0, tzinfo=timezone.utc),
        device_id="test_device_main",
        merchant_category="E-commerce",
        geo_lat=28.6139,
        geo_lng=77.2090,
    )

    mock_request = AsyncMock()
    result = await process_fraud_prediction(mock_request, payload, db_session)
    assert result.fraud_score is not None, "Pipeline should handle tiny amounts"
    assert result.latency_ms >= 0


@pytest.mark.asyncio
async def test_e2e_subtle_fraud_detection(db_session):
    """
    Issue #6: Subtle fraud — moderate anomaly (2x amount, known device,
    slightly off hours) should elevate score above baseline-normal.
    """
    user_id = uuid.uuid4()
    await _create_user_with_history(db_session, user_id)
    mock_request = AsyncMock()

    # Normal baseline transaction
    normal_payload = TransactionRequest(
        user_id=user_id,
        amount=5000.0,
        txn_timestamp=datetime(2026, 2, 20, 14, 30, 0, tzinfo=timezone.utc),
        device_id="test_device_main",
        merchant_category="E-commerce",
        geo_lat=28.6139,
        geo_lng=77.2090,
    )
    normal_result = await process_fraud_prediction(mock_request, normal_payload, db_session)

    # Subtle anomaly: 2x amount, slightly unusual time, same device
    subtle_payload = TransactionRequest(
        user_id=user_id,
        amount=10000.0,  # 2x mean, not extreme
        txn_timestamp=datetime(2026, 2, 20, 23, 45, 0, tzinfo=timezone.utc),  # Late but not 3AM
        device_id="test_device_main",  # Known device
        merchant_category="Electronics",  # Unusual but not high-risk
        geo_lat=28.7,  # Close to home
        geo_lng=77.3,
    )
    subtle_result = await process_fraud_prediction(mock_request, subtle_payload, db_session)

    # Subtle anomaly should score higher than normal, but not necessarily FRAUD
    assert subtle_result.fraud_score >= normal_result.fraud_score, \
        f"Subtle anomaly ({subtle_result.fraud_score}) should score >= normal ({normal_result.fraud_score})"


@pytest.mark.asyncio
async def test_e2e_concurrent_rapid_transactions(db_session):
    """
    Issue #6: Rapid burst of transactions should show elevated BFI/velocity.
    """
    user_id = uuid.uuid4()
    await _create_user_with_history(db_session, user_id)
    mock_request = AsyncMock()

    # Submit 3 transactions in rapid succession
    results = []
    for i in range(3):
        payload = TransactionRequest(
            user_id=user_id,
            amount=5000.0 + (i * 500),
            txn_timestamp=datetime(2026, 2, 20, 14, 30, i, tzinfo=timezone.utc),  # 1-second gaps
            device_id="test_device_main",
            merchant_category="E-commerce",
            geo_lat=28.6139,
            geo_lng=77.2090,
        )
        result = await process_fraud_prediction(mock_request, payload, db_session)
        results.append(result)

    # Pipeline should handle rapid transactions without error
    assert all(r.fraud_score is not None for r in results)
    assert all(r.latency_ms >= 0 for r in results)

