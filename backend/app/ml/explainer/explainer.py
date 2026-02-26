import shap
import numpy as np
import structlog
from typing import List

from app.ml.models.ensemble import ensemble
from app.core.config import settings

logger = structlog.get_logger()

# Human-readable feature descriptions for RBI-compliant explanations
FEATURE_DESCRIPTIONS = {
    # Behavioral indices
    "ADI": "Unusual transaction amount detected",
    "GRI": "Transaction from unfamiliar geographic location",
    "DTS": "Unrecognized or recently-added device used",
    "TRC": "Transaction at unusual time of day",
    "MRS": "Transaction with high-risk merchant category",
    "BFI": "Rapid burst of multiple transactions detected",
    "BDS": "Recipient has prior involvement in flagged transactions",
    "VRI": "Rapid device switching detected within short window",
    "SGAS": "Impossible travel speed between consecutive transactions",
    # Metadata features
    "amount": "Transaction amount is outside normal range",
    "is_weekend": "Weekend transaction pattern detected",
    "hour_of_day": "Transaction hour deviates from typical activity",
    "account_age_days": "Account age is a factor in risk assessment",
    "device_trust_score": "Device trust level contributed to risk",
    "ip_risk_score": "IP address reputation flagged",
    "merchant_risk_score": "Merchant category risk level elevated",
    "beneficiary_risk_score": "Recipient risk profile elevated",
    "velocity_1h": "Short-term transaction velocity is abnormal",
    "velocity_24h": "24-hour transaction volume is unusual",
    "geo_velocity_kmh": "Geographic movement speed between transactions is abnormal",
    "anurupyena_conflict": "Vedic checksum integrity violation detected — potential payload tampering"
}

# Direction-specific templates for richer explanations
INCREASE_TEMPLATES = {
    "ADI": "Transaction amount is {:.1f}× above user baseline average",
    "GRI": "Location is significantly away from trusted transaction zones",
    "DTS": "Device has not been used previously for this account",
    "TRC": "Transaction occurred outside usual active hours (risk window)",
    "MRS": "Merchant category is flagged as high-risk per FinTech risk profiles",
    "BFI": "Multiple transactions detected within 60 seconds (burst pattern)",
    "BDS": "Recipient account has {:.0%} involvement in prior flagged transactions",
    "VRI": "Device was switched within minutes of previous transaction",
    "SGAS": "Implied travel speed between transactions exceeds feasible limits",
    "anurupyena_conflict": "Vedic Anurupyena checksum detected structural anomaly in payload"
}


class ExplainerPipeline:
    """
    Handles local SHAP value generation for explainability as demanded by 
    PRD Section 4.5.3 (Human-in-the-loop Explanation).
    
    Outputs human-readable, RBI-compliant explanations with feature context.
    """
    def __init__(self):
        self._explainer = None
        
    def _initialize_explainer(self):
        """Lazy load TreeExplainer attached to the XGBoost instance."""
        if not ensemble._is_loaded:
            ensemble.load_models()
            
        if self._explainer is None:
            # Standard TreeExplainer attached specifically to XGBoost
            self._explainer = shap.TreeExplainer(ensemble._xgb_model)
            logger.info("shap_explainer_initialized")

    def generate_explanations(self, feature_array: np.ndarray, top_k: int = 3) -> List[str]:
        """
        Calculates SHAP values for the specific transaction and translates 
        the highest deviating features into human-readable explanations.
        
        Output format example:
          "Rapid burst of multiple transactions detected — SHAP impact: +0.234 (risk increased)"
        """
        self._initialize_explainer()
        
        try:
            # Calculate SHAP values
            shap_values = self._explainer.shap_values(feature_array)
            
            # shape could be (1, N) or just (N)
            vals = shap_values[0] if len(shap_values.shape) > 1 else shap_values
            
            # Get feature names and values
            feature_names = ensemble._feature_names
            feature_vals = feature_array[0] if len(feature_array.shape) > 1 else feature_array
            
            # Get indices of top_k absolute biggest impacts
            abs_vals = np.abs(vals)
            top_indices = np.argsort(abs_vals)[-top_k:][::-1]
            
            explanations = []
            for idx in top_indices:
                feat_name = feature_names[idx]
                impact = vals[idx]
                feat_value = feature_vals[idx]
                
                # Human-readable description
                description = FEATURE_DESCRIPTIONS.get(feat_name, f"Feature '{feat_name}' contributed to risk")
                
                # Use rich template if available and impact increases risk
                if impact > 0 and feat_name in INCREASE_TEMPLATES:
                    try:
                        if feat_name == "ADI" and feat_value > 0:
                            description = INCREASE_TEMPLATES[feat_name].format(1 + feat_value * 3)
                        elif feat_name == "BDS" and feat_value > 0:
                            description = INCREASE_TEMPLATES[feat_name].format(feat_value)
                        else:
                            description = INCREASE_TEMPLATES[feat_name]
                    except (ValueError, IndexError):
                        pass  # Fall back to default description
                
                direction = "risk increased" if impact > 0 else "risk decreased"
                explanations.append(
                    f"{description} — SHAP impact: {impact:+.3f} ({direction})"
                )
                
            return explanations
            
        except Exception as e:
            logger.error("shap_explanation_failed", error=str(e))
            return ["Explanation engine encountered an error. Manual review recommended."]

explainer = ExplainerPipeline()
