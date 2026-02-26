from fastapi import APIRouter, Query, Request, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.base import AttackScenarioEnum
from app.models.user import User
from app.services.simulation import stream_attack_simulation
from app.db.session import get_db_session

router = APIRouter()

@router.post("/simulate/attack", summary="Stream Bulk Attack Transactions via NDJSON")
async def simulate_attack(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    attack_type: AttackScenarioEnum = Query(..., description="Type of attack payload"),
    count: int = Query(10, description="Volume to generate (e.g. 1000)"),
    rate_limit_ms: int = Query(50, description="Delay between emissions"),
):
    """
    Simulates high-velocity traffic pumping into the backend API.
    Returns payloads continuously via purely text/plain NDJSON chunks
    preventing heavy JSON allocations from crashing the client.
    """
    
    # Use a real user from the DB so the scoring pipeline can find a baseline
    stmt = select(User.user_id).limit(1)
    result = await db.execute(stmt)
    row = result.first()
    if row is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="No users in database. Run seed_db.py first.")
    target_user = row[0]
    
    payload_generator = stream_attack_simulation(
        session=db,
        scenario=attack_type,
        count=count,
        user_id=target_user,
        rate_limit_ms=rate_limit_ms
    )
    
    return StreamingResponse(
        payload_generator,
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )
