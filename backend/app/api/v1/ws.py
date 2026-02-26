from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import structlog
import asyncio
import uuid
import json
import random

router = APIRouter()
logger = structlog.get_logger()

# Global Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("websocket_connected", total_active=len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("websocket_disconnected", total_active=len(self.active_connections))

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error("ws_broadcast_failed", error=str(e))
                self.disconnect(connection)

manager = ConnectionManager()

@router.websocket("/ws/transactions")
async def websocket_transactions_feed(websocket: WebSocket):
    """
    Maintains a persistent duplex pipeline feeding the React Frontend Dashboard.
    Ideally tied to a Redis Pub/Sub backend, but mocked here with a loop
    pumping synthesized normal transaction metadata sporadically.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Standin for waiting on a Redis Pub/Sub queue 
            await asyncio.sleep(random.uniform(0.5, 3.0))
            
            mock_feed = {
                "type": "NEW_TRANSACTION",
                "payload": {
                    "txn_id": str(uuid.uuid4()),
                    "amount": round(random.uniform(10, 500), 2),
                    "merchant": random.choice(["GROCERY", "RETAIL", "TRANSPORT"]),
                    "risk_band": "SAFE",
                    "fraud_score": random.uniform(0.01, 0.15)
                }
            }
            await manager.broadcast(json.dumps(mock_feed))
            
            # The client could send filters if we implemented receive_text()
            _ = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)

    except asyncio.TimeoutError:
        # Expected ping timeout, ignore & continue loop
        pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error("ws_exception", error=str(e))
        manager.disconnect(websocket)
