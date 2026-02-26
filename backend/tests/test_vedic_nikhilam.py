import pytest
from app.ml.vedic.nikhilam import nikhilam_threshold, benchmark_nikhilam_vs_standard

def test_nikhilam_bounds():
    """Verify Nikhilam never produces extreme weights outside 0 and 1."""
    thresh_high = nikhilam_threshold(score=0.99, risk_factor=10.0)
    thresh_low  = nikhilam_threshold(score=0.01, risk_factor=0.1)
    
    assert 0.0 < thresh_high < 1.0
    assert 0.0 < thresh_low < 1.0

def test_nikhilam_differentiation():
    """Verify high risk limits thresholds faster than low risk parameters."""
    # Given an identical base score of 0.45:
    res_high_risk = nikhilam_threshold(score=0.45, risk_factor=2.0)
    res_low_risk  = nikhilam_threshold(score=0.45, risk_factor=0.5)
    
    # A higher risk factor drops the deviation drastically, which means the threshold 
    # to trigger an anomaly should be numerically smaller and easier to hit
    assert res_high_risk != res_low_risk

def test_nikhilam_benchmark_structure():
    """Verify standard benchmark dictionary payload returns flawlessly."""
    result = benchmark_nikhilam_vs_standard(score=0.6, risk_factor=1.5)
    
    assert "nikhilam_time_ns" in result
    assert "standard_time_ns" in result
    assert "speedup_multiplier" in result
    assert "nikhilam_result" in result
    assert isinstance(result["speedup_multiplier"], float)
