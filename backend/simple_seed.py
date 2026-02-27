"""Simple database seeder that bypasses the complex pipeline"""
import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session_maker, engine
from app.models.user import User
from app.models.transaction import Transaction
from app.models.risk_audit_log import RiskAuditLog
from app.models.base import RiskProfileEnum, RiskBandEnum, ActionTakenEnum
from app.core.security import get_password_hash
import random

async def simple_seed():
    from app.models.base import Base
    import app.models.user
    import app.models.transaction
    import app.models.risk_audit_log

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        # Check if data already exists
        from sqlalchemy import select, func
        result = await session.execute(select(func.count()).select_from(Transaction))
        count = result.scalar()
        if count > 0:
            print(f"Database already has {count} transactions. Skipping seed.")
            return

        print("Creating demo user and transactions...")
        
        # Create demo user
        user_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        user = User(
            user_id=user_id,
            email="demo@vedfin.com",
            hashed_password=get_password_hash("admin123"),
            phone_hash=None,
            risk_profile=RiskProfileEnum.MEDIUM,
            account_age_days=150,
            avg_txn_amount=250.00,
            total_txn_count=50,
            baseline_stats={
                "amount_mean": 250.0,
                "amount_std": 100.0,
                "trusted_devices": ["device_001"],
                "trusted_locations": [{"lat": 28.6139, "lng": 77.2090}],
            },
            trusted_devices=[],
            trusted_locations=[],
            is_deleted=False,
            deleted_at=None,
            created_at=now,
            updated_at=now
        )
        session.add(user)
        await session.flush()

        # Create sample transactions with audit logs
        merchants = ["E-commerce", "Food", "Transport", "Entertainment", "Groceries"]
        base_time = datetime.now(timezone.utc) - timedelta(hours=24)
        
        for i in range(50):
            txn_id = uuid.uuid4()
            is_fraud = i < 8  # 16% fraud rate
            amount = random.uniform(50, 2000) if not is_fraud else random.uniform(500, 5000)
            
            txn = Transaction(
                txn_id=txn_id,
                user_id=user_id,
                amount=round(amount, 2),
                txn_timestamp=base_time + timedelta(minutes=i*30),
                device_id="device_001" if i % 3 != 0 else "device_002",
                device_os="Android",
                ip_subnet="192.168.1.0/24",
                merchant_category=random.choice(merchants),
                merchant_id=f"merchant_{random.randint(1000, 9999)}",
                geo_lat=28.6139 + random.uniform(-0.1, 0.1),
                geo_lng=77.2090 + random.uniform(-0.1, 0.1),
                fraud_label=is_fraud,
                structural_anomalies=None,
                created_at=now,
                updated_at=now
            )
            session.add(txn)
            await session.flush()
            
            # Create audit log for each transaction
            fraud_score = random.uniform(0.7, 0.95) if is_fraud else random.uniform(0.1, 0.4)
            if fraud_score > 0.7:
                risk_band = RiskBandEnum.FRAUD
                action = ActionTakenEnum.BLOCKED
            elif fraud_score > 0.5:
                risk_band = RiskBandEnum.SUSPICIOUS
                action = ActionTakenEnum.HELD
            elif fraud_score > 0.3:
                risk_band = RiskBandEnum.MONITOR
                action = ActionTakenEnum.APPROVED
            else:
                risk_band = RiskBandEnum.SAFE
                action = ActionTakenEnum.APPROVED
            
            audit = RiskAuditLog(
                txn_id=txn_id,
                fraud_score=round(fraud_score, 4),
                risk_band=risk_band,
                action_taken=action,
                latency_ms=random.randint(45, 150),
                model_version="1.0.0",
                behavioral_profile_snapshot={},
                index_scores={
                    "ADI": random.uniform(0.3, 0.8),
                    "GRI": random.uniform(0.2, 0.7),
                    "DTS": random.uniform(0.4, 0.9),
                },
                dynamic_threshold=0.5,
                created_at=now
            )
            session.add(audit)
        
        await session.commit()
        print(f"✅ Seeded 50 transactions ({8} fraud) with audit logs")

if __name__ == "__main__":
    asyncio.run(simple_seed())
