import json
import os
import logging

logger = logging.getLogger(__name__)

REGISTRY_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../models/registry.json'))

class ModelRegistry:
    def __init__(self):
        self._ensure_registry()
        
    def _ensure_registry(self):
        if not os.path.exists(REGISTRY_PATH):
            default_registry = {
                "models": [
                    {
                        "model_name": "xgboost_fraud_model",
                        "model_version": "v2_pre_auth",
                        "feature_schema_version": "v1.0",
                        "training_date": "2026-08-01T00:00:00Z",
                        "training_data_version": "PS_20174392719_1491204439457_log.csv",
                        "evaluation_metrics": {
                            "training_precision": 0.98,
                            "training_recall": 0.85
                        },
                        "status": "ACTIVE"
                    }
                ]
            }
            with open(REGISTRY_PATH, 'w') as f:
                json.dump(default_registry, f, indent=4)
                
    def get_active_model(self):
        with open(REGISTRY_PATH, 'r') as f:
            registry = json.load(f)
            
        for model in registry["models"]:
            if model["status"] == "ACTIVE":
                return model
        return None

    def evaluate_retraining_need(self, drift_results: dict, performance_results: dict):
        """
        Rules:
        - High Feature Drift on >= 2 features -> REVIEW REQUIRED
        - Prediction Drift == HIGH -> RETRAINING RECOMMENDED
        - Live Precision < 0.80 -> RETRAINING RECOMMENDED
        - Otherwise -> MONITOR / NO ACTION
        """
        recommendation = "NO ACTION"
        reasons = []
        
        # 1. Evaluate Performance
        if performance_results.get("status") == "SUCCESS":
            precision = performance_results["metrics"].get("precision", 1.0)
            if precision < 0.80:
                recommendation = "RETRAINING RECOMMENDED"
                reasons.append(f"Live precision dropped to {precision:.2f}")
                
        # 2. Evaluate Prediction Drift
        pred_drift = drift_results.get("prediction_drift")
        if pred_drift and pred_drift.get("severity") == "HIGH":
            recommendation = "RETRAINING RECOMMENDED"
            reasons.append("Prediction distribution shows HIGH drift.")
            
        # 3. Evaluate Feature Drift
        features = drift_results.get("features", [])
        high_drift_count = sum(1 for f in features if f.get("severity") == "HIGH")
        
        if high_drift_count >= 2 and recommendation != "RETRAINING RECOMMENDED":
            recommendation = "REVIEW REQUIRED"
            reasons.append(f"{high_drift_count} features show HIGH drift.")
        elif high_drift_count > 0 and recommendation == "NO ACTION":
            recommendation = "MONITOR"
            reasons.append("Some features show drift. Monitor closely.")
            
        return {
            "recommendation": recommendation,
            "reasons": reasons
        }

model_registry = ModelRegistry()
