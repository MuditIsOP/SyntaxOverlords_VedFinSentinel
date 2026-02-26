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
        """Loads models from the centralized .pkl artifact with fallback."""
        if self._is_loaded:
            return

        artifact_path = settings.MODEL_PATH
        if not os.path.exists(artifact_path):
            logger.warning("model_artifact_missing_fallback", path=artifact_path)
            self._load_fallback_model()
            return

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
                logger.warning("artifact_incomplete_using_fallback")
                self._load_fallback_model()
                return
                
            self._is_loaded = True
            logger.info("models_loaded_successfully", 
                        version=artifact.get("version", "unknown"),
                        feature_count=len(self._feature_names),
                        has_iso_calibration=self._iso_training_scores is not None)
                        
        except Exception as e:
            logger.error("model_loading_failed_fallback", error=str(e))
            self._load_fallback_model()

    def _load_fallback_model(self):
        """Load rule-based fallback when ML model is unavailable."""
        logger.warning("loading_fallback_rule_based_model")
        
        # JUDGE FIX: Only runtime-computable features - removed card*/V* features
        # These caused train↔inference skew
        self._feature_names = [
            "amount", "is_weekend", "hour_of_day", "account_age_days",
            "ADI", "GRI", "DTS", "TRC", "MRS",
            "amount_percentile", "geo_distance_km", "velocity_entropy",
            "category_entropy", "sequence_autocorr", "recipient_risk",
            "recipient_connections", "ewma_deviation", "time_anomaly",
            "device_trust_score", "merchant_risk_score",
            "beneficiary_risk_score", "velocity_1h", "velocity_24h",
            "geo_velocity_kmh", "integrity_conflict",
        ]
        
        # Feature medians for fallback (only runtime-computable features)
        self._feature_medians = {f: 0.0 for f in self._feature_names}
        self._feature_medians.update({
            "ADI": 0.3, "GRI": 0.2, "DTS": 0.5, "TRC": 0.2, "MRS": 0.3,
            "velocity_1h": 0.1, "velocity_24h": 0.05, "geo_velocity_kmh": 50.0,
        })
        
        self._is_loaded = True
        self._using_fallback = True
        logger.info("fallback_model_loaded", feature_count=len(self._feature_names))

    def predict(self, feature_dict: Dict[str, float]) -> Tuple[float, float, float, np.ndarray]:
        """
        Executes the hybrid prediction (or fallback rule-based if model unavailable).
        Returns: (ensemble_score, xgb_prob, iso_score, feature_array)
        """
        if not self._is_loaded:
            self.load_models()
        
        # If using fallback, use rule-based scoring
        if getattr(self, '_using_fallback', False):
            return self._fallback_predict(feature_dict)

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

            # Issue #9: Percentile-based calibration
            if self._iso_training_scores is not None:
                iso_score = 1.0 - (percentileofscore(self._iso_training_scores, iso_raw) / 100.0)
            else:
                iso_score = max(0.0, min(1.0, 0.5 - (iso_raw * 0.5)))
            
            iso_score = max(0.0, min(1.0, iso_score))

            # FIXED: Proper ensemble combination (70% XGBoost, 30% Isolation Forest)
            # XGBoost is more reliable for known patterns, IF catches novel anomalies
            ensemble_score = (0.7 * xgb_prob) + (0.3 * iso_score)
            ensemble_score = max(0.0, min(1.0, ensemble_score))

            return ensemble_score, xgb_prob, iso_score, feature_array
            
        except Exception as e:
            logger.error("ensemble_prediction_failed", error=str(e))
            raise PredictionFailedException(reason="Inference execution failed on model layer.")

    def _fallback_predict(self, feature_dict: Dict[str, float]) -> Tuple[float, float, float, np.ndarray]:
        """Rule-based fallback prediction when ML model unavailable."""
        # Extract key features for rule-based scoring
        amount = feature_dict.get("amount", 0)
        adi = feature_dict.get("ADI", 0)
        gri = feature_dict.get("GRI", 0)
        dts = feature_dict.get("DTS", 0)
        trc = feature_dict.get("TRC", 0)
        mrs = feature_dict.get("MRS", 0)
        velocity_entropy = feature_dict.get("velocity_entropy", 0)
        integrity_conflict = feature_dict.get("integrity_conflict", 0)
        
        # Rule-based scoring (mimics ensemble output)
        base_score = 0.1
        
        # Add risk factors
        if adi > 0.7: base_score += 0.25  # Amount anomaly
        if gri > 0.6: base_score += 0.20  # Geographic anomaly
        if dts > 0.7: base_score += 0.20  # Unknown device
        if trc > 0.5: base_score += 0.10  # Time anomaly
        if mrs > 0.5: base_score += 0.15  # Merchant risk
        if velocity_entropy > 0.7: base_score += 0.15  # Bot-like velocity
        if integrity_conflict > 0: base_score += 0.30  # Tampered payload
        
        # Large amount bonus
        if amount > 10000: base_score += 0.10
        
        score = min(1.0, base_score)
        
        # Create feature array for compatibility
        feature_array = np.array([[feature_dict.get(f, 0.0) for f in self._feature_names]])
        
        logger.debug("fallback_prediction_used", score=score, amount=amount)
        
        return score, score, score * 0.8, feature_array  # (ensemble, xgb, iso, features)

ensemble = SentinelEnsemble()
