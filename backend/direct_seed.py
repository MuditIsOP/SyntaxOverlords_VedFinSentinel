# Direct SQLite seeder - uses exact model schema
import asyncio
import uuid
import random
import hashlib
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, func, text

DB_PATH = "sqlite+aiosqlite:///./vedfin_local.db"
engine = create_async_engine(DB_PATH, echo=False)
session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def seed():
    from app.models.base import Base
    import app.models.user
    import app.models.transaction
    import app.models.risk_audit_log

    from app.models.user import User
    from app.models.transaction import Transaction
    from app.models.risk_audit_log import RiskAuditLog
    from app.models.base import RiskProfileEnum as RPE, RiskBandEnum as RBE, ActionTakenEnum as ATE, ReviewerStatusEnum as RSE
    from app.core.security import get_password_hash

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables ensured.")

    async with session_maker() as session:
        result = await session.execute(select(func.count()).select_from(Transaction))
        count = result.scalar()
        if count and count > 0:
            print("DB has " + str(count) + " transactions. Clearing and reseeding...")
            await session.execute(text("DELETE FROM risk_audit_logs"))
            await session.execute(text("DELETE FROM transactions"))
            await session.execute(text("DELETE FROM users"))
            await session.commit()

        print("Seeding demo data...")
        now = datetime.now(timezone.utc)
        user_id = uuid.uuid4()

        user = User(
            user_id=user_id,
            email="demo@vedfin.com",
            hashed_password=get_password_hash("admin123"),
            phone_hash=None,
            risk_profile=RPE.MEDIUM,
            account_age_days=180,
            avg_txn_amount=280.00,
            total_txn_count=100,
            baseline_stats={
                "amount_mean": 280.0,
                "amount_std": 120.0,
                "trusted_devices": ["device_001"],
                "trusted_locations": [{"lat": 28.6139, "lng": 77.2090}],
            },
            trusted_devices=["device_001"],
            trusted_locations=[{"lat": 28.6139, "lng": 77.2090}],
            is_deleted=False,
        )
        session.add(user)
        await session.flush()

        merchants = ["E-commerce", "Food", "Transport", "Entertainment", "Groceries", "Healthcare", "Travel", "Utilities"]
        base_time = now - timedelta(hours=23, minutes=45)
        total = 0

        for i in range(80):
            txn_id = uuid.uuid4()
            is_fraud = i < 18

            if is_fraud:
                amount = round(random.uniform(800, 8000), 2)
                device = "device_unknown_" + str(random.randint(1, 5))
                lat = 28.6139 + random.uniform(5.0, 15.0)
            else:
                amount = round(random.uniform(50, 1500), 2)
                device = "device_001" if i % 4 != 0 else "device_002"
                lat = 28.6139 + random.uniform(-0.1, 0.1)

            ts = base_time + timedelta(minutes=i * 18)

            txn = Transaction(
                txn_id=txn_id,
                user_id=user_id,
                amount=amount,
                txn_timestamp=ts,
                device_id=device,
                device_os="Android" if not is_fraud else "Unknown",
                ip_subnet="192.168.1.0/24" if not is_fraud else "10.0.0.0/8",
                merchant_category=random.choice(merchants),
                merchant_id="MRC" + str(random.randint(1000, 9999)),
                geo_lat=lat,
                geo_lng=77.2090 + random.uniform(-0.1, 0.1),
                fraud_label=is_fraud,
                structural_anomalies=["amount_spike", "geo_anomaly"] if is_fraud else None,
            )
            session.add(txn)
            await session.flush()

            if is_fraud:
                fraud_score = round(random.uniform(0.72, 0.97), 4)
                xgb = round(random.uniform(0.65, 0.95), 4)
                iso = round(random.uniform(0.60, 0.90), 4)
                risk_band = RBE.FRAUD if fraud_score > 0.80 else RBE.SUSPICIOUS
                action = ATE.BLOCKED if risk_band == RBE.FRAUD else ATE.HELD
                explanation = "High geo deviation + unknown device + amount spike detected."
            else:
                fraud_score = round(random.uniform(0.05, 0.42), 4)
                xgb = round(random.uniform(0.02, 0.38), 4)
                iso = round(random.uniform(0.03, 0.40), 4)
                risk_band = RBE.MONITOR if fraud_score > 0.30 else RBE.SAFE
                action = ATE.APPROVED
                explanation = "Transaction within normal behavioral parameters."

            idx = {
                "ADI": round(random.uniform(0.7 if is_fraud else 0.2, 0.95 if is_fraud else 0.45), 3),
                "GRI": round(random.uniform(0.6 if is_fraud else 0.05, 0.90 if is_fraud else 0.35), 3),
                "DTS": round(random.uniform(0.05 if is_fraud else 0.55, 0.35 if is_fraud else 0.92), 3),
                "TRC": round(random.uniform(0.2, 0.6), 3),
                "VRI": round(random.uniform(0.5 if is_fraud else 0.05, 0.88 if is_fraud else 0.38), 3),
                "BDS": round(random.uniform(0.2, 0.7), 3),
            }

            log_hash = hashlib.sha256((str(txn_id) + str(fraud_score)).encode()).hexdigest()

            audit = RiskAuditLog(
                txn_id=txn_id,
                fraud_score=fraud_score,
                risk_band=risk_band,
                action_taken=action,
                latency_ms=random.randint(38, 155),
                log_hash=log_hash,
                human_explanation=explanation,
                shap_values=idx,
                index_scores=idx,
                dynamic_threshold=0.5,
                xgboost_score=xgb,
                isolation_score=iso,
                ensemble_weight_xgb=0.7,
                reviewer_status=RSE.PENDING,
                created_at=ts,
            )
            session.add(audit)
            total += 1

        await session.commit()
        print("SUCCESS: Seeded " + str(total) + " transactions (18 fraud, " + str(total - 18) + " legit)")
        print("Demo login -> email: demo@vedfin.com | password: admin123")

if __name__ == "__main__":
    asyncio.run(seed())
