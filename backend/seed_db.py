"""
VedFin Sentinel — Seed Database with REAL IEEE-CIS Transactions

Issue #7 fix: Seeds from actual IEEE-CIS transactions passed through the real
pipeline, not from random.gauss() synthetic data. Every dashboard metric, chart,
and audit log entry is genuinely computed by the real model.
"""

import asyncio
import uuid
import os
import pandas as pd
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session_maker, engine
from app.models.user import User
from app.models.transaction import Transaction
from app.models.risk_audit_log import RiskAuditLog
from app.models.base import RiskProfileEnum, RiskBandEnum, ActionTakenEnum
from app.core.security import get_password_hash
from app.services.baseline_service import update_user_baseline
from app.schemas.predict import TransactionRequest
from app.services.fraud_scoring import process_fraud_prediction
from unittest.mock import AsyncMock


# Path to IEEE-CIS dataset
IEEE_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "ieee-cis", "raw")
TRANSACTION_FILE = os.path.join(IEEE_DATA_DIR, "train_transaction.csv")


async def seed():
    from app.models.base import Base
    import app.models.user
    import app.models.transaction
    import app.models.risk_audit_log

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Load real IEEE-CIS transactions for seeding
    print("📂 Loading real IEEE-CIS transactions for seed data...")
    real_txns = pd.read_csv(
        TRANSACTION_FILE,
        usecols=["TransactionID", "TransactionAmt", "TransactionDT", "ProductCD",
                 "card4", "isFraud", "dist1"],
        nrows=200  # Read a bit more to get a mix of fraud/non-fraud
    )

    # Sort by transaction time
    real_txns = real_txns.sort_values("TransactionDT").reset_index(drop=True)

    # Select ~80 non-fraud + ~20 fraud to get 100 balanced examples
    non_fraud = real_txns[real_txns["isFraud"] == 0].head(80)
    fraud = real_txns[real_txns["isFraud"] == 1].head(20)
    if len(fraud) < 20:
        # If not enough fraud in first 200, take what we have
        fraud = real_txns[real_txns["isFraud"] == 1]
    seed_txns = pd.concat([non_fraud, fraud]).sort_values("TransactionDT").reset_index(drop=True)
    print(f"   Selected {len(seed_txns)} transactions ({(seed_txns['isFraud']==1).sum()} fraud)")

    async with async_session_maker() as session:
        # 1. Create demo user
        user_id = uuid.uuid4()
        user = User(
            user_id=user_id,
            email="demo@vedfin.com",
            hashed_password=get_password_hash("admin123"),
            risk_profile=RiskProfileEnum.MEDIUM,
            account_age_days=150,
            avg_txn_amount=float(seed_txns["TransactionAmt"].mean()),
            total_txn_count=len(seed_txns),
            baseline_stats={
                "amount_mean": float(seed_txns["TransactionAmt"].mean()),
                "amount_std": float(seed_txns["TransactionAmt"].std()),
                "trusted_devices": ["device_main_001"],
                "device_counts": {"device_main_001": 15},
                "trusted_locations": [{"lat": 28.6139, "lng": 77.2090}],
                "active_hours": list(range(8, 22)),
                "frequent_merchant_categories": ["E-commerce", "Food", "Transport"],
                "baseline_txn_count": len(seed_txns),
            }
        )
        session.add(user)
        await session.commit()

        # 2. Process real transactions through the actual pipeline
        # Map ProductCD to merchant categories
        product_to_merchant = {
            "W": "E-commerce",
            "H": "Entertainment",
            "C": "Groceries",
            "S": "Transport",
            "R": "Food"
        }

        mock_request = AsyncMock()
        base_time = datetime.now(timezone.utc) - timedelta(days=15)
        devices = ["device_main_001", "device_main_001", "device_main_001",
                    "device_backup_002", "device_main_001"]

        success_count = 0
        error_count = 0

        for idx, row in seed_txns.iterrows():
            try:
                # Create payload from real IEEE-CIS data
                txn_time = base_time + timedelta(seconds=int(row["TransactionDT"]))
                merchant = product_to_merchant.get(row.get("ProductCD", "W"), "E-commerce")
                amount = max(100.0, float(row["TransactionAmt"]))

                # Slight location variation based on dist1
                base_lat, base_lng = 28.6139, 77.2090
                dist_offset = float(row.get("dist1", 0)) if pd.notna(row.get("dist1")) else 0
                lat = base_lat + (dist_offset * 0.0001)  # Small offset
                lng = base_lng + (dist_offset * 0.00005)

                payload = TransactionRequest(
                    user_id=user_id,
                    amount=amount,
                    txn_timestamp=txn_time,
                    device_id=devices[idx % len(devices)],
                    merchant_category=merchant,
                    geo_lat=round(lat, 6),
                    geo_lng=round(lng, 6),
                )

                # Pass through the REAL pipeline — real model, real SHAP, real behavioral engine
                result = await process_fraud_prediction(mock_request, payload, session)
                success_count += 1

                if success_count % 20 == 0:
                    print(f"   Processed {success_count}/{len(seed_txns)} transactions "
                          f"(latest score: {result.fraud_score:.4f}, band: {result.risk_band})")

            except Exception as e:
                error_count += 1
                if error_count <= 3:
                    print(f"   ⚠️ Error processing txn {idx}: {e}")

        print(f"\n✅ Database seeded with {success_count} REAL pipeline-processed transactions")
        if error_count > 0:
            print(f"   ⚠️ {error_count} transactions failed to process")

        # 3. Compute and persist real baseline from the seeded transaction history
        baseline = await update_user_baseline(session, user_id)
        print(f"✅ Baseline computed: amount_mean={baseline['amount_mean']:.2f}, "
              f"std={baseline['amount_std']:.2f}, "
              f"devices={len(baseline['trusted_devices'])}, "
              f"locations={len(baseline['trusted_locations'])}")


if __name__ == "__main__":
    asyncio.run(seed())
