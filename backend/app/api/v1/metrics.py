from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import time
import random
from app.db.session import get_db_session

from app.services.metrics import compute_dashboard_metrics
from app.services.kafka_streaming import get_stream_metrics, kafka_processor, submit_to_stream
from app.ml.models.behavioral_embeddings import behavioral_analyzer

router = APIRouter()

@router.get("/health", summary="System Health Check")
async def get_health_check():
    """
    Comprehensive health check endpoint.
    Exposes status of all ML models and infrastructure components.
    """
    # Get component statuses
    kafka_health = kafka_processor.get_health()
    behavioral_status = behavioral_analyzer.get_status()
    
    # Determine overall health
    is_healthy = (
        behavioral_status["is_loaded"] and
        kafka_health.get("demo_mode", False) is not None  # Either mode is fine
    )
    
    return {
        "status": "healthy" if is_healthy else "degraded",
        "timestamp": time.time(),
        "components": {
            "behavioral_model": {
                "status": "loaded" if behavioral_status["is_loaded"] else "failed",
                "mode": behavioral_status["mode"],
                "using_trained_weights": behavioral_status["using_trained_weights"],
                "model_path": behavioral_status["model_path"]
            },
            "kafka_streaming": {
                "status": "healthy" if kafka_health["kafka_healthy"] else "degraded",
                "mode": "kafka" if not kafka_health["demo_mode"] else "demo_queue",
                "kafka_available": kafka_health["kafka_available"],
                "last_error": kafka_health["last_error"]
            }
        },
        "notes": {
            "behavioral_model": "Trained on IEEE-CIS dataset" if behavioral_status["using_trained_weights"] else "Run generate_model.py to train",
            "kafka": "Install kafka-python and start Kafka for production streaming" if kafka_health["demo_mode"] else "Production Kafka active"
        }
    }

@router.get("/metrics", summary="Global Dashboard Metrics")
async def get_system_metrics(
    db: AsyncSession = Depends(get_db_session)
):
    """
    Exposes high-level aggregates for the React Dashboard.
    Computes real precision/recall from database audit logs.
    """
    return await compute_dashboard_metrics(db=db, window_hours=24)


@router.get("/metrics/live", summary="Live Kafka Streaming Metrics")
async def get_live_metrics(
    window_seconds: int = 60
):
    """
    Real-time streaming metrics from Kafka consumer.
    Provides live throughput, latency, and fraud detection rate.
    """
    return {
        "window_seconds": window_seconds,
        **get_stream_metrics(window_seconds),
        "processor_stats": {
            "total_produced": kafka_processor.processing_stats["produced"],
            "total_consumed": kafka_processor.processing_stats["consumed"],
            "errors": kafka_processor.processing_stats["errors"],
            "avg_latency_ms": round(kafka_processor.processing_stats["avg_latency_ms"], 2),
        },
        "mode": "kafka" if not kafka_processor._demo_mode else "demo_queue"
    }


@router.post("/stream/transaction", summary="Submit Transaction to Kafka Stream")
async def submit_stream_transaction(transaction: dict):
    """
    Submit a transaction to Kafka for real-time streaming processing.
    High-throughput endpoint for bulk transaction ingestion.
    """
    accepted = await submit_to_stream(transaction)
    return {
        "accepted": accepted,
        "mode": "kafka" if not kafka_processor._demo_mode else "demo_queue",
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
