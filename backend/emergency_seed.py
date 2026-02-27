"""Emergency database seeder using raw SQL"""
import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import engine
from sqlalchemy import text
import random

async def emergency_seed():
    async with engine.begin() as conn:
        # Check current counts
        result = await conn.execute(text("SELECT COUNT(*) FROM transactions"))
        txn_count = result.scalar()
        print(f"Current transactions: {txn_count}")
        
        if txn_count > 0:
            print("Database already seeded.")
            return
        
        print("Creating data via raw SQL...")
        
        # Create user
        user_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        await conn.execute(text("""
            INSERT INTO users (user_id, email, hashed_password, phone_hash, risk_profile, 
                             baseline_stats, account_age_days, trusted_devices, trusted_locations,
                             avg_txn_amount, total_txn_count, is_deleted, deleted_at, created_at, updated_at)
            VALUES (:uid, :email, :pwd, NULL, 'MEDIUM', :stats, 150, '[]'::jsonb, '[]'::jsonb, 
                    250.00, 50, false, NULL, :ts, :ts)
        """), {
            "uid": user_id,
            "email": "demo@vedfin.com",
            "pwd": "$5$rounds=535000$x$xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",  # dummy
            "stats": '{"amount_mean": 250.0, "amount_std": 100.0}',
            "ts": now
        })
        
        merchants = ["E-commerce", "Food", "Transport", "Entertainment", "Groceries"]
        base_time = datetime.now(timezone.utc) - timedelta(hours=24)
        
        for i in range(50):
            txn_id = str(uuid.uuid4())
            is_fraud = i < 8
            amount = random.uniform(50, 2000) if not is_fraud else random.uniform(500, 5000)
            txn_time = (base_time + timedelta(minutes=i*30)).isoformat()
            device = "device_001" if i % 3 != 0 else "device_002"
            merchant = random.choice(merchants)
            
            await conn.execute(text("""
                INSERT INTO transactions (txn_id, user_id, amount, txn_timestamp, device_id, device_os,
                    ip_subnet, merchant_category, merchant_id, geo_lat, geo_lng, fraud_label, 
                    structural_anomalies, created_at, updated_at)
                VALUES (:tid, :uid, :amt, :ts, :dev, 'Android', '192.168.1.0/24', :mcat, :mid,
                    :lat, :lng, :fraud, NULL, :now, :now)
            """), {
                "tid": txn_id,
                "uid": user_id,
                "amt": round(amount, 2),
                "ts": txn_time,
                "dev": device,
                "mcat": merchant,
                "mid": f"merchant_{random.randint(1000, 9999)}",
                "lat": 28.6139 + random.uniform(-0.1, 0.1),
                "lng": 77.2090 + random.uniform(-0.1, 0.1),
                "fraud": is_fraud,
                "now": now
            })
            
            # Create audit log
            fraud_score = random.uniform(0.7, 0.95) if is_fraud else random.uniform(0.1, 0.4)
            if fraud_score > 0.7:
                risk_band, action = 'FRAUD', 'BLOCKED'
            elif fraud_score > 0.5:
                risk_band, action = 'SUSPICIOUS', 'HELD'
            elif fraud_score > 0.3:
                risk_band, action = 'MONITOR', 'ALLOWED'
            else:
                risk_band, action = 'SAFE', 'ALLOWED'
            
            await conn.execute(text("""
                INSERT INTO risk_audit_logs (txn_id, fraud_score, risk_band, action_taken, latency_ms,
                    model_version, behavioral_profile_snapshot, index_scores, dynamic_threshold, created_at)
                VALUES (:tid, :score, :band, :action, :lat, '1.0.0', '{}', :idx, 0.5, :ts)
            """), {
                "tid": txn_id,
                "score": round(fraud_score, 4),
                "band": risk_band,
                "action": action,
                "lat": random.randint(45, 150),
                "idx": '{"ADI": 0.5, "GRI": 0.5, "DTS": 0.5}',
                "ts": now
            })
        
        print(f"✅ Seeded 50 transactions ({8} fraud)")

if __name__ == "__main__":
    asyncio.run(emergency_seed())
