import pytest
from datetime import datetime, timezone, timedelta
from app.services.behavioral import (
    compute_adi, compute_gri, compute_dts, compute_trc, compute_mrs,
    compute_bfi, compute_bds, compute_vri, compute_sgas
)

class MockTransaction:
    def __init__(self, ts, device="dev1", lat=0.0, lng=0.0):
        self.txn_timestamp = ts
        self.device_id = device
        self.geo_lat = lat
        self.geo_lng = lng

def test_compute_adi():
    baseline = {"amount_mean": 1000, "amount_std": 200}
    assert compute_adi(1000, baseline) == 0.0 # exactly mean
    assert compute_adi(1600, baseline) == 1.0 # 3 std devs away
    assert compute_adi(2000, baseline) == 1.0 # above 3 bounded to 1.0

def test_compute_gri():
    baseline = {"trusted_locations": [{"lat": 12.9, "lng": 77.5}]}
    # Same location
    assert compute_gri(12.9, 77.5, baseline) < 0.1 
    # Missing location
    assert compute_gri(None, None, baseline) == 0.5
    # Far away (London vs Bangalore)
    assert compute_gri(51.5, -0.1, baseline) == 1.0

def test_compute_dts():
    baseline = {"trusted_devices": ["iphone-12", "macbook-pro"]}
    assert compute_dts("iphone-12", baseline) == 0.0
    assert compute_dts("unknown-android", baseline) == 1.0

def test_compute_trc():
    baseline = {"active_hours": [9, 10, 11, 12, 13, 14, 15, 16, 17]}
    # Safe hour 10 AM
    ts_safe = datetime(2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    assert compute_trc(ts_safe, baseline) == 0.0
    
    # Suspicious hour 3 AM
    ts_sus = datetime(2023, 1, 1, 3, 0, 0, tzinfo=timezone.utc)
    assert compute_trc(ts_sus, baseline) == 0.8

def test_compute_mrs():
    assert compute_mrs("GAMBLING", {}) == 0.95
    assert compute_mrs("GROCERY", {"frequent_merchant_categories": ["GROCERY"]}) == 0.0
    assert compute_mrs("UNKNOWN", {}) == 0.3

def test_compute_bfi():
    now = datetime.now(timezone.utc)
    recent = [
        MockTransaction(now - timedelta(seconds=10)),
        MockTransaction(now - timedelta(seconds=20)),
        MockTransaction(now - timedelta(seconds=40)), # 3 txns in 40 seconds
    ]
    assert compute_bfi(recent, now) == 1.0
    
    recent_slow = [
        MockTransaction(now - timedelta(seconds=1000)),
        MockTransaction(now - timedelta(seconds=2000)),
        MockTransaction(now - timedelta(seconds=3000)), 
    ]
    assert compute_bfi(recent_slow, now) == 0.0

def test_compute_bds():
    # BDS is now async and DB-backed — tested in test_integration.py
    # Here we only verify the import works
    import inspect
    assert inspect.iscoroutinefunction(compute_bds)

def test_compute_vri():
    now = datetime.now(timezone.utc)
    # Changing device rapidly
    recent = [MockTransaction(now - timedelta(minutes=5), device="dev1")]
    assert compute_vri(recent, "dev2") == 0.8 

def test_compute_sgas():
    now = datetime.now(timezone.utc)
    # Bangalore
    recent = [MockTransaction(now - timedelta(minutes=10), lat=12.9, lng=77.5)]
    # 10 minutes later in London (impossible travel)
    assert compute_sgas(recent, 51.5, -0.1) == 1.0
