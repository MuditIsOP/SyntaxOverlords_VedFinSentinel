import os
import pickle
import numpy as np
import xgboost as xgb
from sklearn.ensemble import IsolationForest

def build_dummy_ensemble():
    """
    Simulates the ML pipeline by creating lightweight, but functional estimators
    exported as a unified .pkl artifact per the DesignDoc specifications.
    This fulfills the requirement so the backend API inference can boot correctly.
    """
    print("Building Synthetic Feature Array...")
    # 21 predefined features exactly strictly matching 5.3 Hybrid Sentinel Ensemble
    feature_names = [
        "amount", "is_weekend", "hour_of_day", "account_age_days",
        "ADI", "GRI", "DTS", "TRC", "MRS", "BFI", "BDS", "VRI", "SGAS",
        "device_trust_score", "ip_risk_score", "merchant_risk_score",
        "beneficiary_risk_score", "velocity_1h", "velocity_24h",
        "geo_velocity_kmh", "anurupyena_conflict"
    ]
    
    # 500 rows, 21 columns
    X_dummy = np.random.rand(500, 21)
    # Target (1 = fraud, 0 = legitimate)
    y_dummy = np.random.randint(0, 2, size=500)

    print("Training XGBoost Classifier...")
    # XGBoost setup using specified PRD rules
    xgb_model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        # SMOTE implication -> Scale positive weight for class imbalances
        scale_pos_weight=10, 
        eval_metric='logloss',
        random_state=42
    )
    xgb_model.fit(X_dummy, y_dummy)

    print("Training Isolation Forest Anomaly Detector...")
    # Isolation Forest setup
    iso_model = IsolationForest(
        n_estimators=100,
        contamination=0.05,  # Expected 5% anomaly rate
        random_state=42
    )
    iso_model.fit(X_dummy)

    print("Aggregating Artifact Payload...")
    ensemble_artifact = {
        "xgboost": xgb_model,
        "isolation_forest": iso_model,
        "feature_names": feature_names,
        "version": "1.0.0"
    }

    # Ensure target directory exists
    artifact_dir = os.path.dirname(__file__)
    target_path = os.path.join(artifact_dir, "..", "artifacts", "sentinel_ensemble.pkl")
    os.makedirs(os.path.dirname(target_path), exist_ok=True)

    print(f"Exporting Sentinel Ensemble to {target_path}...")
    with open(target_path, "wb") as f:
        pickle.dump(ensemble_artifact, f)
        
    print("Pipeline Complete. Artifact Ready for Inference.")

if __name__ == "__main__":
    build_dummy_ensemble()
