import asyncio
import json
import uuid
import random
from datetime import datetime, timezone, timedelta
from typing import AsyncGenerator

from app.schemas.predict import TransactionRequest
from app.models.base import AttackScenarioEnum

def generate_attack_payload(scenario: AttackScenarioEnum, base_user_id: uuid.UUID, iteration: int = 0) -> tuple[TransactionRequest, dict]:
    """
    Generates realistic attack payloads matching PRD scenarios.
    
    Scenarios:
    - GEO_SPOOFING/IMPOSSIBLE_TRAVEL: Rapid location changes (VPN, proxy hopping)
    - BURST_MICRO/VELOCITY_BURST: High-frequency small transactions (card testing)
    - ACCOUNT_TAKEOVER/INTEGRITY_ATTACK: New device + new location + high value
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)  # Naive datetime to match database
    
    # Map aliases to base scenarios
    scenario_map = {
        AttackScenarioEnum.VELOCITY_BURST: AttackScenarioEnum.BURST_MICRO,
        AttackScenarioEnum.IMPOSSIBLE_TRAVEL: AttackScenarioEnum.GEO_SPOOFING,
        AttackScenarioEnum.INTEGRITY_ATTACK: AttackScenarioEnum.ACCOUNT_TAKEOVER,
    }
    # Use mapped scenario if it's an alias, otherwise use original
    effective_scenario = scenario_map.get(scenario, scenario)
    
    # Location pools for realistic scenarios
    INDIA_LOCATIONS = [
        {"city": "Mumbai", "lat": 19.0760, "lng": 72.8777},
        {"city": "Delhi", "lat": 28.6139, "lng": 77.2090},
        {"city": "Bangalore", "lat": 12.9716, "lng": 77.5946},
        {"city": "Chennai", "lat": 13.0827, "lng": 80.2707},
    ]
    
    FOREIGN_LOCATIONS = [
        {"city": "New York", "lat": 40.7128, "lng": -74.0060},
        {"city": "London", "lat": 51.5074, "lng": -0.1278},
        {"city": "Singapore", "lat": 1.3521, "lng": 103.8198},
        {"city": "Dubai", "lat": 25.2048, "lng": 55.2708},
    ]
    
    if effective_scenario == AttackScenarioEnum.BURST_MICRO:
        # Card testing: small amounts, rapid fire, same device
        # PRD: 50 transactions under ₹999 in 3 minutes
        payload = TransactionRequest(
            user_id=base_user_id,
            amount=round(random.uniform(100, 999), 2),  # Under ₹999
            txn_timestamp=now - timedelta(seconds=iteration * 3),  # Every 3 seconds
            geo_lat=INDIA_LOCATIONS[0]["lat"],  # Same location
            geo_lng=INDIA_LOCATIONS[0]["lng"],
            device_id="burst-test-device",
            device_os="android",
            merchant_category="GIFT_CARDS"  # High risk category
        )
        return payload, {"scenario": "burst_micro", "iteration": iteration, "city": "Mumbai"}
        
    elif effective_scenario == AttackScenarioEnum.GEO_SPOOFING:
        # VPN/proxy hopping: same transaction, different countries rapidly
        # Alternate between India and foreign locations
        is_foreign = iteration % 2 == 1
        loc_pool = FOREIGN_LOCATIONS if is_foreign else INDIA_LOCATIONS
        loc = loc_pool[iteration % len(loc_pool)]
        
        payload = TransactionRequest(
            user_id=base_user_id,
            amount=round(random.uniform(1000, 5000), 2),
            txn_timestamp=now - timedelta(minutes=iteration * 2),  # Every 2 minutes
            geo_lat=loc["lat"],
            geo_lng=loc["lng"],
            device_id="geo-spoof-vpn",
            device_os="ios",
            merchant_category="CRYPTO"
        )
        return payload, {"scenario": "geo_spoofing", "iteration": iteration, "city": loc["city"], "is_foreign": is_foreign}
        
    elif effective_scenario == AttackScenarioEnum.ACCOUNT_TAKEOVER:
        # New device, new location, unknown recipient, high value
        loc = random.choice(FOREIGN_LOCATIONS)
        
        # Progressive escalation in ATO scenario
        if iteration == 0:
            # First: device change from trusted location
            amount = 500
            merchant = "GROCERY"
        elif iteration == 1:
            # Second: new location + new device
            amount = 5000
            merchant = "ELECTRONICS"
        else:
            # Third: high value to unknown recipient
            amount = 49500
            merchant = "CRYPTO"
            
        payload = TransactionRequest(
            user_id=base_user_id,
            amount=amount,
            txn_timestamp=now - timedelta(minutes=iteration * 5),
            geo_lat=loc["lat"],
            geo_lng=loc["lng"],
            device_id="ato-new-device-xyz",
            device_os="web",  # Suspicious: web vs mobile app
            merchant_category=merchant,
            recipient_id=uuid.uuid4()  # Unknown recipient
        )
        return payload, {"scenario": "account_takeover", "iteration": iteration, "city": loc["city"], "stage": ["device_change", "geo_change", "high_value"][min(iteration, 2)]}
    else:
        # Fallback to normal transaction
        loc = random.choice(INDIA_LOCATIONS)
        payload = TransactionRequest(
            user_id=base_user_id,
            amount=500.00,
            txn_timestamp=now,
            geo_lat=loc["lat"],
            geo_lng=loc["lng"],
            device_id="normal-device",
            merchant_category="GROCERY"
        )
        return payload, {"scenario": "normal", "city": loc["city"]}

from app.services.fraud_scoring import process_fraud_prediction
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

async def stream_attack_simulation(
    session_factory: async_sessionmaker,
    scenario: AttackScenarioEnum,
    count: int,
    user_id: uuid.UUID,
    rate_limit_ms: int
) -> AsyncGenerator[str, None]:
    """Generates NDJSON stream of realistic attack vectors matching PRD scenarios."""
    from fastapi import Request
    mock_request = type('Request', (), {'headers': {}, 'client': type('Client', (), {'host': '127.0.0.1'})()})()

    for i in range(count):
        # FIXED: Pass iteration for progressive scenarios
        payload, meta = generate_attack_payload(scenario, user_id, iteration=i)
        
        # Use a fresh session for each transaction to avoid session state issues
        async with session_factory() as session:
            try:
                res = await process_fraud_prediction(mock_request, payload, session)
                
                res_dict = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "stage": "SIMULATING",
                    "scenario": meta.get("scenario"),
                    "iteration": i,
                    "details": f"{scenario.name} | {meta.get('city', 'N/A')} | Stage: {meta.get('stage', 'N/A')}",
                    "txn_id": str(res.txn_id),
                    "fraud_score": float(res.fraud_score),
                    "risk_band": res.risk_band,
                    "action_taken": res.action_taken,
                    "reasons": res.reasons,
                }
                
                yield json.dumps(res_dict) + "\n"
            except Exception as e:
                import traceback
                error_detail = f"{type(e).__name__}: {str(e)}"
                logger.error("attack_simulation_failed", iteration=i, error=error_detail, traceback=traceback.format_exc())
                yield json.dumps({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "stage": "ERROR",
                    "error": error_detail,
                    "iteration": i
                }) + "\n"
            
        await asyncio.sleep(rate_limit_ms / 1000.0)
    
    # Signal completion
    yield json.dumps({"stage": "COMPLETE", "total": count}) + "\n"
