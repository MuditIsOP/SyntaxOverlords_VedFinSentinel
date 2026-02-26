import asyncio
import json
import uuid
import random
from datetime import datetime, timezone, timedelta
from typing import AsyncGenerator

from app.schemas.predict import TransactionRequest
from app.models.base import AttackScenarioEnum

def generate_attack_payload(scenario: AttackScenarioEnum, base_user_id: uuid.UUID) -> tuple[TransactionRequest, dict]:
    """Generates a malicious transaction mimicking specific topologies. Returns (Payload, Meta)"""
    now = datetime.now(timezone.utc)
    
    # Regional/Global Location Pool
    locations = [
        {"city": "Mumbai", "lat": 19.0760, "lng": 72.8777},
        {"city": "New York", "lat": 40.7128, "lng": -74.0060},
        {"city": "London", "lat": 51.5074, "lng": -0.1278},
        {"city": "Singapore", "lat": 1.3521, "lng": 103.8198},
        {"city": "Dubai", "lat": 25.2048, "lng": 55.2708},
        {"city": "Chennai", "lat": 13.0827, "lng": 80.2707},
        {"city": "Delhi", "lat": 28.6139, "lng": 77.2090},
    ]
    
    loc = random.choice(locations)
    
    if scenario == AttackScenarioEnum.VELOCITY_BURST:
        payload = TransactionRequest(
            user_id=base_user_id,
            amount=round(random.uniform(10, 50), 2),
            txn_timestamp=now,
            geo_lat=loc["lat"],
            geo_lng=loc["lng"],
            device_id="anomalous-script-bot",
            merchant_category="GIFT_CARDS"
        )
        return payload, loc
    elif scenario == AttackScenarioEnum.IMPOSSIBLE_TRAVEL:
        target = random.choice([l for l in locations if l["city"] != "London"])
        is_london = random.choice([True, False])
        active_loc = {"city": "London", "lat": 51.5074, "lng": -0.1278} if is_london else target
        payload = TransactionRequest(
            user_id=base_user_id,
            amount=round(random.uniform(100, 1000), 2),
            txn_timestamp=now,
            geo_lat=active_loc["lat"], 
            geo_lng=active_loc["lng"],
            device_id="stolen-session",
            merchant_category="ELECTRONICS"
        )
        return payload, active_loc
    elif scenario == AttackScenarioEnum.VEDIC_COLLISION:
        payload = TransactionRequest(
            user_id=base_user_id,
            amount=9999.99,
            txn_timestamp=now,
            geo_lat=0.0,
            geo_lng=0.0,
            device_id="vedic-spoof",
            merchant_category="WIRE_TRANSFER"
        )
        return payload, {"city": "Vedic Virtual Hub", "lat": 0.0, "lng": 0.0}
    else:
        payload = TransactionRequest(
            user_id=base_user_id,
            amount=25.00,
            txn_timestamp=now,
            geo_lat=loc["lat"],
            geo_lng=loc["lng"],
            device_id="known-device",
            merchant_category="GROCERY"
        )
        return payload, loc

from app.services.fraud_scoring import process_fraud_prediction
from sqlalchemy.ext.asyncio import AsyncSession

async def stream_attack_simulation(
    session: AsyncSession,
    scenario: AttackScenarioEnum,
    count: int,
    user_id: uuid.UUID,
    rate_limit_ms: int
) -> AsyncGenerator[str, None]:
    """Generates NDJSON (Newline Delimited JSON) stream of attack vectors."""
    # Mock request for the scoring pipeline
    from fastapi import Request
    # Create a minimal mock request
    mock_request = type('Request', (), {'headers': {}, 'client': type('Client', (), {'host': '127.0.0.1'})()})()

    for i in range(count):
        payload, loc = generate_attack_payload(scenario, user_id)
        
        # Execute real prediction
        try:
            res = await process_fraud_prediction(mock_request, payload, session)
            
            res_dict = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "stage": "SIMULATING",
                "details": f"Processed {scenario.name} in {loc['city']} | Result: {res.risk_band} | Action: {res.action_taken} | Reasons: {', '.join(res.reasons)}",
                "txn_id": str(res.txn_id),
                "fraud_score": float(res.fraud_score),
                "risk_band": res.risk_band,
                "action_taken": res.action_taken,
                "reasons": res.reasons,
                "scenario_tag": scenario.name,
                "iteration": i
            }
            
            yield json.dumps(res_dict) + "\n"
        except Exception as e:
            yield json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "stage": "ERROR",
                "details": f"Fault in scoring pipeline: {str(e)}",
                "iteration": i
            }) + "\n"
            
        await asyncio.sleep(rate_limit_ms / 1000.0)

