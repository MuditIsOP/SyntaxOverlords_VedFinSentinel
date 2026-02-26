from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
import structlog

from app.schemas.predict import TransactionRequest, FraudScoreResponse
from app.services.fraud_scoring import process_fraud_prediction
from app.services.attack_simulation import attack_runner
from app.core.dependencies import VerifiedToken

from app.db.session import get_db_session

router = APIRouter()
logger = structlog.get_logger()

@router.post("/predict", response_model=FraudScoreResponse, summary="Synchronous Fraud Scoring API")
async def predict_transaction(
    request: Request,
    payload: TransactionRequest,
    token: VerifiedToken,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Evaluates a single transaction comprehensively utilizing XGBoost, 
    Isolation Forest, SHAP, and statistical behavioral features.
    Returns HTTP 200 strictly formatted by `FraudScoreResponse`.
    """
    logger.info("predict_request_received", mapped_user=str(payload.user_id))
    return await process_fraud_prediction(request, payload, db)

@router.post("/bulk_predict", response_model=List[FraudScoreResponse], summary="Batch Fraud Scoring API")
async def bulk_predict_transactions(
    request: Request,
    payloads: List[TransactionRequest],
    token: VerifiedToken,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Evaluates multiple transactions. Extremely heavy on computational load.
    Will utilize the exact same flow sequentially for safety, though standard deployments
    might optimize batch matrix multiplication.
    """
    logger.info("bulk_predict_request_received", batch_size=len(payloads))
    
    results = []
    for tx in payloads:
        res = await process_fraud_prediction(request, tx, db)
        results.append(res)
        
    return results


@router.post("/simulate/attack", summary="Attack Simulation Lab")
async def simulate_attack(
    attack_type: str,
    user_id: UUID,
    num_transactions: int = 10
):
    """
    Attack Simulation Laboratory - Run realistic attack scenarios.
    
    Available attack types:
    - card_testing: Rapid small transactions to test stolen cards
    - account_takeover: Transactions from new devices/locations  
    - velocity_burst: Burst of transactions in short time window
    - impossible_travel: Impossible travel patterns
    - merchant_fraud: Suspicious merchant category patterns
    
    Returns detailed detection results for demo purposes.
    """
    logger.info("attack_simulation_requested", attack_type=attack_type, user_id=str(user_id))
    
    result = await attack_runner.run_simulation(
        attack_type=attack_type,
        user_id=user_id,
        num_transactions=num_transactions
    )
    
    return result


@router.post("/simulate/all", summary="Run All Attack Simulations")
async def simulate_all_attacks(user_id: UUID):
    """
    Run all attack types and return comprehensive detection results.
    This is the "Heist & Catch" demo endpoint for the hackathon.
    """
    logger.info("full_attack_simulation_requested", user_id=str(user_id))
    
    results = await attack_runner.run_all_simulations(user_id)
    
    # Calculate overall detection rate
    total_attacks = sum(r["total_transactions"] for r in results)
    total_detected = sum(r["fraud_detected"] for r in results)
    
    return {
        "demo_title": "The Heist & Catch - Attack Simulation Laboratory",
        "user_id": str(user_id),
        "total_simulations": len(results),
        "overall_detection_rate": total_detected / total_attacks if total_attacks > 0 else 0,
        "simulations": results
    }
