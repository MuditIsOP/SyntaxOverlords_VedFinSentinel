from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import structlog

from app.schemas.predict import TransactionRequest, FraudScoreResponse
from app.services.fraud_scoring import process_fraud_prediction
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
    Isolation Forest, SHAP, Behavioral features, and Vedic Mathematics constraints.
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
