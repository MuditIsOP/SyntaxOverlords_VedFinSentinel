"""
FIXED WebSocket: Real-time transaction streaming from database.
Replaces the mocked random data with actual transaction + audit log data.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.orm import joinedload
import structlog
import asyncio
import json
from datetime import datetime, timezone
from typing import List

from app.db.session import async_session_factory
from app.models.transaction import Transaction
from app.models.risk_audit_log import RiskAuditLog

router = APIRouter()
logger = structlog.get_logger()


class ConnectionManager:
    """Manages WebSocket connections for real-time transaction feed."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("websocket_connected", total_active=len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("websocket_disconnected", total_active=len(self.active_connections))

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                error_msg = str(e)
                # Silently handle normal disconnects (1000) and already-closed connections
                if "1000" in error_msg or "close message has been sent" in error_msg:
                    disconnected.append(connection)
                else:
                    logger.error("ws_broadcast_failed", error=error_msg)
                    disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()


async def fetch_recent_transactions(limit: int = 10) -> List[dict]:
    """Fetch recent transactions with their audit data from DB."""
    async with async_session_factory() as session:
        stmt = (
            select(Transaction, RiskAuditLog)
            .join(RiskAuditLog, Transaction.txn_id == RiskAuditLog.txn_id, isouter=True)
            .order_by(desc(Transaction.txn_timestamp))
            .limit(limit)
        )
        result = await session.execute(stmt)
        rows = result.all()

        transactions = []
        for txn, audit in rows:
            transactions.append({
                "txn_id": str(txn.txn_id),
                "amount": float(txn.amount),
                "merchant_category": txn.merchant_category,
                "risk_band": audit.risk_band.name if audit else "PENDING",
                "fraud_score": float(audit.fraud_score) if audit else 0.0,
                "timestamp": txn.txn_timestamp.isoformat() if txn.txn_timestamp else datetime.now(timezone.utc).isoformat(),
                "action": audit.action_taken.name if audit else "PENDING",
            })
        return transactions


async def poll_new_transactions(last_id: str = None, poll_interval: float = 0.5):
    """Poll database for new transactions and yield them."""
    while True:
        try:
            async with async_session_factory() as session:
                stmt = (
                    select(Transaction, RiskAuditLog)
                    .join(RiskAuditLog, Transaction.txn_id == RiskAuditLog.txn_id, isouter=True)
                    .order_by(desc(Transaction.txn_timestamp))
                    .limit(1)
                )
                result = await session.execute(stmt)
                row = result.first()

                if row:
                    txn, audit = row
                    txn_id_str = str(txn.txn_id)

                    if txn_id_str != last_id:
                        last_id = txn_id_str
                        yield {
                            "type": "NEW_TRANSACTION",
                            "payload": {
                                "txn_id": txn_id_str,
                                "amount": float(txn.amount),
                                "merchant_category": txn.merchant_category,
                                "risk_band": audit.risk_band.name if audit else "PENDING",
                                "fraud_score": float(audit.fraud_score) if audit else 0.0,
                                "timestamp": txn.txn_timestamp.isoformat() if txn.txn_timestamp else datetime.now(timezone.utc).isoformat(),
                                "action": audit.action_taken.name if audit else "PENDING",
                            }
                        }
            await asyncio.sleep(poll_interval)
        except Exception as e:
            logger.error("ws_poll_error", error=str(e))
            await asyncio.sleep(poll_interval)


@router.websocket("/ws/transactions")
async def websocket_transactions_feed(websocket: WebSocket):
    """
    FIXED: Real-time WebSocket streaming actual transaction data from database.
    Streams recent transactions on connection, then new transactions as they're created.
    """
    await manager.connect(websocket)
    last_id = None

    try:
        # Send recent history on connect
        recent = await fetch_recent_transactions(limit=10)
        for txn in reversed(recent):
            await websocket.send_text(json.dumps({
                "type": "HISTORY",
                "payload": txn
            }))
            last_id = txn["txn_id"]

        # Stream new transactions
        async for event in poll_new_transactions(last_id=last_id):
            await manager.broadcast(json.dumps(event))

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error("websocket_error", error=str(e))
        manager.disconnect(websocket)
