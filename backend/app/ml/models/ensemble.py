import os
import pickle
import numpy as np
import xgboost as xgb
from sklearn.ensemble import IsolationForest
from scipy.stats import percentileofscore
import structlog
from typing import Dict, Any, Tuple

from app.core.config import settings
from app.core.exceptions import PredictionFailedException

logger = structlog.get_logger()

class SentinelEnsemble:
    """
    Singleton handler for loading and executing the hybrid Sentinel model
    (XGBoost + Isolation Forest) as specified in PRD Section 5.3.

    Issue #9 fix: Isolation Forest scores are calibrated using percentile-based
    normalization against training set scores (stored in the model artifact).
    """
    _instance = None
    _xgb_model = None
    _iso_model = None
    _feature_names = None
    _iso_training_scores = None
    _feature_medians = None  # Issue #2: population-level feature medians for inference
    _is_loaded = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SentinelEnsemble, cls).__new__(cls)
        return cls._instance

    def load_models(self):
        """Loads models from the centralized .pkl artifact."""
        if self._is_loaded:
            return

        artifact_path = settings.MODEL_PATH
        if not os.path.exists(artifact_path):
            logger.error("model_artifact_missing", path=artifact_path)
            raise PredictionFailedException(reason=f"Model artifact not found at {artifact_path}")

        try:
            with open(artifact_path, "rb") as f:
                artifact = pickle.load(f)
                
            self._xgb_model = artifact.get("xgboost")
            self._iso_model = artifact.get("isolation_forest")
            self._feature_names = artifact.get("feature_names")
            # Issue #9: Load training IF scores for percentile calibration
            self._iso_training_scores = artifact.get("iso_training_scores")
            # Issue #2: Load feature medians for runtime inference defaults
            self._feature_medians = artifact.get("feature_medians", {})
            
            if not all([self._xgb_model, self._iso_model, self._feature_names]):
                raise ValueError("Artifact missing required model keys")
                
            self._is_loaded = True
            logger.info("models_loaded_successfully", 
                        version=artifact.get("version", "unknown"),
                        feature_count=len(self._feature_names),
                        has_iso_calibration=self._iso_training_scores is not None)
                        
        except Exception as e:
            logger.error("model_loading_failed", error=str(e))
            raise PredictionFailedException(reason="Failed to load model artifact into memory.")

    def predict(self, feature_dict: Dict[str, float]) -> Tuple[float, float, np.ndarray]:
        """
        Executes the hybrid prediction.
        Returns: (xgb_prob, iso_score, feature_array)

        Issue #9: iso_score is now calibrated using percentileofscore
        against training set IF scores, giving a proper 0-1 probability.
        """
        if not self._is_loaded:
            self.load_models()

        # Map dictionary to strictly ordered array based on training feature_names
        try:
            feature_array = np.array([[feature_dict.get(f, 0.0) for f in self._feature_names]])
        except Exception as e:
            logger.error("feature_mapping_failed", error=str(e))
            raise PredictionFailedException(reason="Input feature dictionary map failed.")

        # Execute predictions
        try:
            # XGBoost probability of Fraud (Class 1)
            xgb_prob = float(self._xgb_model.predict_proba(feature_array)[0][1])
            
            # Isolation Forest anomaly score
            iso_raw = float(self._iso_model.decision_function(feature_array)[0])

            # Issue #9: Percentile-based calibration instead of arbitrary linear mapping
            # Lower/more-negative decision_function = more anomalous
            # percentileofscore gives the % of training samples LESS anomalous
            # We invert so higher = more anomalous
            if self._iso_training_scores is not None:
                iso_score = 1.0 - (percentileofscore(self._iso_training_scores, iso_raw) / 100.0)
            else:
                # Fallback to old mapping if no calibration data
                iso_score = max(0.0, min(1.0, 0.5 - (iso_raw * 0.5)))
            
            iso_score = max(0.0, min(1.0, iso_score))

            return xgb_prob, iso_score, feature_array
            
        except Exception as e:
            logger.error("ensemble_prediction_failed", error=str(e))
            raise PredictionFailedException(reason="Inference execution failed on model layer.")

ensemble = SentinelEnsemble()
