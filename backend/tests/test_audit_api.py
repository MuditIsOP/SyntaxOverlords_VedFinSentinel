import pytest
from fastapi.testclient import TestClient
from main import app
import uuid

client = TestClient(app)

def test_metrics_endpoint():
    res = client.get("/api/v1/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "system_health" in data
    assert data["system_health"] == "OPTIMAL"

def test_audit_logs_endpoint():
    res = client.get("/api/v1/audit/logs?limit=10")
    # Returns an empty list in our mock, but 200 OK structural 
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_audit_export_csv():
    res = client.get("/api/v1/audit/export?format=csv")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert b"txn_id,fraud_score,action,timestamp" in res.content

def test_user_baseline_endpoint():
    u_id = str(uuid.uuid4())
    res = client.get(f"/api/v1/users/{u_id}/baseline")
    assert res.status_code == 200
    data = res.json()
    assert "risk_profile" in data
    
    reset_res = client.post(f"/api/v1/users/{u_id}/baseline/reset")
    assert reset_res.status_code == 200
    assert reset_res.json()["status"] == "success"
