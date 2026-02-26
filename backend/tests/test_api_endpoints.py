import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_websocket_feed_connects():
    """Verify WebSocket upgrades correctly on the target endpoint."""
    with client.websocket_connect("/api/v1/ws/transactions") as websocket:
        # Send minimal payload manually to trigger duplex wait mechanism in router
        websocket.send_text("PING")
        
        # We shouldn't disconnect instantly
        assert websocket is not None

def test_health_check_via_testclient():
    """Ensure TestClient standard connectivity passes overall API structure."""
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
