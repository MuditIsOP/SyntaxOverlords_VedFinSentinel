import pytest
import uuid
import json
from app.api.v1.simulate import simulate_attack
from app.services.simulation import stream_attack_simulation
from app.models.base import AttackScenarioEnum

@pytest.mark.asyncio
async def test_attack_simulation_generator():
    test_user = uuid.uuid4()
    
    # Fire the async generator mapped to geo-impossibility attack
    gen = stream_attack_simulation(
        scenario=AttackScenarioEnum.IMPOSSIBLE_TRAVEL,
        count=3,
        user_id=test_user,
        rate_limit_ms=1
    )
    
    results = []
    async for payload in gen:
        # Should be a newline delimited standard json string
        parsed = json.loads(payload.strip())
        results.append(parsed)
        
    assert len(results) == 3
    assert results[0]["risk_band"] == "FRAUD"
    assert results[0]["scenario_tag"] == "IMPOSSIBLE_TRAVEL"
