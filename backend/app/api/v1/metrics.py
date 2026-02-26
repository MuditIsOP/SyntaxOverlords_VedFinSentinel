from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import time
import random
from app.db.session import get_db_session

from app.services.metrics import compute_dashboard_metrics
from app.services.streaming import get_stream_metrics, stream_processor

router = APIRouter()

@router.get("/metrics", summary="Global Dashboard Metrics")
async def get_system_metrics(
    db: AsyncSession = Depends(get_db_session)
):
    """
    Exposes high-level aggregates for the React Dashboard.
    Computes real precision/recall from database audit logs.
    """
    return await compute_dashboard_metrics(db=db, window_hours=24)


@router.get("/metrics/live", summary="Live Streaming Metrics")
async def get_live_metrics(
    window_seconds: int = 60
):
    """
    Real-time streaming metrics from sliding window.
    Provides live throughput, latency, and fraud detection rate.
    """
    return {
        "window_seconds": window_seconds,
        **get_stream_metrics(window_seconds),
        "processor_stats": {
            "total_processed": stream_processor.processing_stats["processed"],
            "errors": stream_processor.processing_stats["errors"],
            "avg_latency_ms": round(stream_processor.processing_stats["avg_latency_ms"], 2),
            "current_throughput_tps": round(stream_processor.processing_stats["throughput_tps"], 2)
        }
    }


@router.post("/stream/transaction", summary="Submit Transaction to Stream")
async def submit_stream_transaction(transaction: dict):
    """
    Submit a transaction for real-time streaming processing.
    High-throughput endpoint for bulk transaction ingestion.
    """
    accepted = await stream_processor.submit_transaction(transaction)
    return {
        "accepted": accepted,
        "queue_size": stream_processor.transaction_queue.qsize(),
        "timestamp": time.time()
    }


@router.get("/metrics/precision-recall", summary="Live Precision/Recall Metrics")
async def get_precision_recall_metrics(
    db: AsyncSession = Depends(get_db_session),
    window_hours: int = 24
):
    """
    Compute live precision/recall metrics from actual predictions.
    This is the key deliverable for the hackathon problem statement.
    """
    metrics = await compute_dashboard_metrics(db=db, window_hours=window_hours)
    
    return {
        "window_hours": window_hours,
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "f1_score": metrics["f1_score"],
        "false_positive_rate": metrics["false_positive_rate"],
        "confusion_matrix": metrics["confusion_matrix"],
        "total_evaluated": metrics["total_transactions"],
        "methodology": "Computed from actual RiskAuditLog vs Transaction ground truth",
        "verification": "These are operational metrics, not training metrics"
    }
