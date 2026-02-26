import asyncio
import os
import sys
from uuid import uuid4

# Setup path so modules from app/ can be accessed
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.user import User
from app.models.base import RiskProfileEnum

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://vedfinuser:password@localhost:5432/vedfindb")

async def seed_users():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        users = [
            User(
                email="user1_low_risk@example.com",
                phone_hash="hash1",
                risk_profile=RiskProfileEnum.LOW,
                baseline_stats={
                    "adi": {"mean": 1000, "std": 100},
                    "trc": {"active_hours_start": 8, "active_hours_end": 20}
                },
                avg_txn_amount=1000,
                total_txn_count=50
            ),
            User(
                email="user2_med_risk@example.com",
                phone_hash="hash2",
                risk_profile=RiskProfileEnum.MEDIUM,
                baseline_stats={
                    "adi": {"mean": 5000, "std": 1500},
                    "trc": {"active_hours_start": 9, "active_hours_end": 22}
                },
                avg_txn_amount=5000,
                total_txn_count=120
            ),
            User(
                email="user3_high_risk@example.com",
                phone_hash="hash3",
                risk_profile=RiskProfileEnum.HIGH,
                baseline_stats={
                    "adi": {"mean": 20000, "std": 8000},
                    "trc": {"active_hours_start": 0, "active_hours_end": 23}
                },
                avg_txn_amount=20000,
                total_txn_count=15
            )
        ]
        
        session.add_all(users)
        await session.commit()
        print("Successfully seeded 3 demo users!")

if __name__ == "__main__":
    asyncio.run(seed_users())
