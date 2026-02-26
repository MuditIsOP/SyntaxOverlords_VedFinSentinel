"""
Streaming Transaction Processing Infrastructure

Provides real-time streaming capability using in-memory queues for high-throughput processing.
In production, this would use Kafka. For the demo/hackathon, we use asyncio queues.
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable
from collections import deque
import structlog

logger = structlog.get_logger()


class TransactionStreamProcessor:
    """
    Real-time transaction stream processor.
    
    Features:
    - Async queue-based processing
    - Sliding window aggregation
    - Real-time anomaly detection
    - High-throughput batching
    """
    
    def __init__(self, max_queue_size: int = 10000, workers: int = 4):
        self.transaction_queue = asyncio.Queue(maxsize=max_queue_size)
        self.workers = workers
        self.is_running = False
        self.processing_stats = {
            "processed": 0,
            "errors": 0,
            "avg_latency_ms": 0.0,
            "throughput_tps": 0.0
        }
        
        # Sliding window for real-time metrics
        self._window_size = 1000
        self._recent_predictions = deque(maxlen=self._window_size)
        self._window_start_time = datetime.now(timezone.utc)
    
    async def start(self, processor_fn: Callable):
        """Start the stream processor with given processing function."""
        self.is_running = True
        self._window_start_time = datetime.now(timezone.utc)
        
        # Start worker tasks
        tasks = [
            asyncio.create_task(self._worker(processor_fn, i))
            for i in range(self.workers)
        ]
        
        logger.info("stream_processor_started", workers=self.workers)
        return tasks
    
    async def _worker(self, processor_fn: Callable, worker_id: int):
        """Worker task that processes transactions from the queue."""
        while self.is_running:
            try:
                # Get transaction with timeout
                transaction = await asyncio.wait_for(
                    self.transaction_queue.get(), 
                    timeout=1.0
                )
                
                start_time = datetime.now(timezone.utc)
                
                # Process transaction
                result = await processor_fn(transaction)
                
                # Track metrics
                latency_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
                self._update_stats(latency_ms, result)
                
                self.transaction_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error("stream_processing_error", worker_id=worker_id, error=str(e))
                self.processing_stats["errors"] += 1
    
    def _update_stats(self, latency_ms: float, result: Dict[str, Any]):
        """Update processing statistics."""
        self.processing_stats["processed"] += 1
        
        # Update average latency
        n = self.processing_stats["processed"]
        old_avg = self.processing_stats["avg_latency_ms"]
        self.processing_stats["avg_latency_ms"] = (
            (old_avg * (n - 1) + latency_ms) / n
        )
        
        # Update throughput (transactions per second in current window)
        time_elapsed = (datetime.now(timezone.utc) - self._window_start_time).total_seconds()
        if time_elapsed > 0:
            self.processing_stats["throughput_tps"] = n / time_elapsed
        
        # Store prediction for sliding window metrics
        self._recent_predictions.append({
            "fraud_score": result.get("fraud_score", 0),
            "risk_band": result.get("risk_band", "SAFE"),
            "latency_ms": latency_ms,
            "timestamp": datetime.now(timezone.utc)
        })
    
    async def submit_transaction(self, transaction: Dict[str, Any]) -> bool:
        """Submit a transaction to the processing queue."""
        try:
            await asyncio.wait_for(
                self.transaction_queue.put(transaction),
                timeout=0.1
            )
            return True
        except asyncio.TimeoutError:
            logger.warning("stream_queue_full", queue_size=self.transaction_queue.qsize())
            return False
    
    def get_sliding_window_metrics(self, window_seconds: int = 60) -> Dict[str, Any]:
        """
        Compute metrics from recent predictions in sliding window.
        
        Returns real-time precision/recall based on risk band predictions.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
        recent = [p for p in self._recent_predictions if p["timestamp"] > cutoff]
        
        if not recent:
            return {
                "window_size": 0,
                "fraud_detected": 0,
                "safe_count": 0,
                "avg_latency_ms": 0,
                "fraud_rate": 0.0
            }
        
        # Count by risk band
        fraud_count = sum(1 for p in recent if p["risk_band"] in ["FRAUD", "SUSPICIOUS"])
        safe_count = sum(1 for p in recent if p["risk_band"] == "SAFE")
        
        avg_latency = sum(p["latency_ms"] for p in recent) / len(recent)
        
        return {
            "window_size": len(recent),
            "fraud_detected": fraud_count,
            "safe_count": safe_count,
            "avg_latency_ms": round(avg_latency, 2),
            "fraud_rate": fraud_count / len(recent),
            "throughput_tps": len(recent) / window_seconds
        }
    
    async def stop(self):
        """Stop the stream processor."""
        self.is_running = False
        await self.transaction_queue.join()
        logger.info("stream_processor_stopped", stats=self.processing_stats)


# Singleton instance
stream_processor = TransactionStreamProcessor(workers=4)


class KafkaSimulator:
    """
    Simulates Kafka-like streaming for the hackathon demo.
    In production, replace with actual Kafka producer/consumer.
    """
    
    def __init__(self):
        self.topics: Dict[str, asyncio.Queue] = {}
        self.consumers: Dict[str, list] = {}
    
    async def create_topic(self, topic_name: str, partitions: int = 1):
        """Create a new topic (simulated)."""
        if topic_name not in self.topics:
            self.topics[topic_name] = asyncio.Queue(maxsize=10000)
            self.consumers[topic_name] = []
            logger.info("kafka_topic_created", topic=topic_name, partitions=partitions)
    
    async def produce(self, topic: str, message: Dict[str, Any], key: Optional[str] = None):
        """Produce a message to a topic."""
        if topic not in self.topics:
            await self.create_topic(topic)
        
        payload = {
            "key": key or str(datetime.now(timezone.utc).timestamp()),
            "value": json.dumps(message),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "partition": 0
        }
        
        try:
            await asyncio.wait_for(self.topics[topic].put(payload), timeout=0.5)
            return True
        except asyncio.TimeoutError:
            logger.warning("kafka_produce_timeout", topic=topic)
            return False
    
    async def consume(self, topic: str, group_id: str, processor: Callable):
        """Consume messages from a topic."""
        if topic not in self.topics:
            await self.create_topic(topic)
        
        consumer_id = f"{group_id}_{len(self.consumers[topic])}"
        self.consumers[topic].append(consumer_id)
        
        logger.info("kafka_consumer_started", topic=topic, consumer_id=consumer_id)
        
        while True:
            try:
                message = await asyncio.wait_for(
                    self.topics[topic].get(),
                    timeout=1.0
                )
                
                # Process message
                data = json.loads(message["value"])
                await processor(data)
                
                self.topics[topic].task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error("kafka_consume_error", topic=topic, error=str(e))


# Kafka simulator singleton (for demo purposes)
kafka_simulator = KafkaSimulator()


# Convenience function for high-throughput processing
async def submit_to_stream(transaction: Dict[str, Any]) -> bool:
    """
    Submit a transaction for real-time streaming processing.
    Returns True if accepted, False if queue is full.
    """
    return await stream_processor.submit_transaction(transaction)


async def get_stream_metrics(window_seconds: int = 60) -> Dict[str, Any]:
    """Get current streaming metrics from sliding window."""
    return stream_processor.get_sliding_window_metrics(window_seconds)


# For compatibility with datetime imports
from datetime import timedelta
