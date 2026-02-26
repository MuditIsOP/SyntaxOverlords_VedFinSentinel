import pytest
from app.ml.vedic.anurupyena import compute_anurupyena_checksum
from datetime import datetime, timezone

def test_anurupyena_checksum_deterministic():
    """Verify the exact same checksum is produced for the same inputs constantly."""
    ts = datetime.now(timezone.utc).isoformat()
    
    run_1 = compute_anurupyena_checksum(
        amount=500.25, timestamp_iso=ts, geo_lat=12.9716, geo_lng=77.5946
    )
    
    run_2 = compute_anurupyena_checksum(
        amount=500.25, timestamp_iso=ts, geo_lat=12.9716, geo_lng=77.5946
    )
    assert run_1 == run_2

def test_anurupyena_checksum_variant_amounts():
    """Verify different amounts mutate the string hash output."""
    ts = datetime.now(timezone.utc).isoformat()
    
    hash_1 = compute_anurupyena_checksum(500.25, ts, 12.9716, 77.5946)
    hash_2 = compute_anurupyena_checksum(500.26, ts, 12.9716, 77.5946)
    
    assert hash_1 != hash_2

def test_anurupyena_checksum_zero_handling():
    """Verify zero or invalid parameters gracefully produce a hash without throwing."""
    ts = "invalid-date-string"
    
    res = compute_anurupyena_checksum(
        amount=-100, timestamp_iso=ts, geo_lat=None, geo_lng=None
    )
    # Should produce a valid vedic checksum string (not crash)
    assert isinstance(res, str)
    assert res.startswith("vedic:")

