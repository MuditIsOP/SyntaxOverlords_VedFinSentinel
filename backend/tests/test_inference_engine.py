import pytest
import numpy as np
from app.ml.models.ensemble import ensemble
from app.ml.explainer.explainer import explainer
from app.core.exceptions import PredictionFailedException

def test_ensemble_prediction_flow(monkeypatch):
    """Verifies that the ensemble correctly transforms dicts and outputs bounds."""
    # Since we can't guarantee train.py was run locally before test suite,
    # we mock the models for structural testing.
    
    class MockXGB:
        def predict_proba(self, arr):
            return np.array([[0.2, 0.8]]) # [Safe, Fraud]
            
    class MockISO:
        def decision_function(self, arr):
            return np.array([-0.1])
            
    # Mock loaded state
    ensemble._is_loaded = True
    ensemble._xgb_model = MockXGB()
    ensemble._iso_model = MockISO()
    ensemble._feature_names = ["ADI", "GRI"]
    
    xgb_prob, iso_score, arr = ensemble.predict({"ADI": 1.0, "GRI": 0.5})
    
    assert xgb_prob == 0.8
    assert 0.0 <= iso_score <= 1.0 # Verify normalization math
    assert arr.shape == (1, 2)
    assert arr[0][0] == 1.0 # Map order verification

def test_shap_explanation_formatting(monkeypatch):
    """Verify SHAP translates array data into readable risk strings."""
    class MockExplainer:
        def shap_values(self, arr):
            return np.array([0.5, -0.3, 0.1, 0.8])
            
    # Prime Explainer with mocks
    explainer._explainer = MockExplainer()
    ensemble._feature_names = ["F1", "F2", "F3", "F4"]
    
    dummy_arr = np.zeros((1, 4))
    reasons = explainer.generate_explanations(dummy_arr, top_k=2)
    
    assert len(reasons) == 2
    # Highest absolute impact is index 3 (0.8), followed by index 0 (0.5)
    assert "F4 increased risk" in reasons[0]
    assert "F1 increased risk" in reasons[1]
