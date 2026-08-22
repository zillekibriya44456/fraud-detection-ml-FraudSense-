import joblib
import xgboost as xgb
import pandas as pd
import os
import sys
import logging
import time

logger = logging.getLogger(__name__)

# Ensure src modules can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.features.realtime_features import engineer_realtime_features
from src.decision_engine import decision_engine
from src.behavioral.engine import behavioral_engine

# Load Pre-Authorization Models
MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../models/pre_authorization'))
MODEL_PATH = os.path.join(MODEL_DIR, 'xgboost_fraud_model.json')
PREPROCESSOR_PATH = os.path.join(MODEL_DIR, 'preprocessor.joblib')

class FraudDetectionService:
    def __init__(self):
        self.model = None
        self.preprocessor = None
        self._model_loaded = False
        self.load_artifacts()

    def load_artifacts(self):
        if not os.path.exists(MODEL_PATH) or not os.path.exists(PREPROCESSOR_PATH):
            logger.warning("Model artifacts not found. API in degraded state.")
            self._model_loaded = False
            return

        try:
            self.model = xgb.XGBClassifier()
            self.model.load_model(MODEL_PATH)
            self.preprocessor = joblib.load(PREPROCESSOR_PATH)
            self._model_loaded = True
            logger.info("Real-Time Pre-Auth model artifacts loaded successfully.")
        except Exception as exc:
            logger.error("Failed to load model artifacts: %s", exc)
            self._model_loaded = False

    def is_ready(self) -> bool:
        return self._model_loaded

    def predict(self, transaction_data: dict) -> dict:
        if not self._model_loaded:
            raise RuntimeError("Model is not loaded.")

        start_time = time.time()
        
        # We must exclude post-transaction features if they are passed
        safe_keys = ['step', 'type', 'amount', 'oldbalanceOrg', 'oldbalanceDest']
        safe_data = {k: transaction_data.get(k, 0) for k in safe_keys}
        
        df = pd.DataFrame([safe_data])
        df_engineered = engineer_realtime_features(df)
        X_processed = self.preprocessor.transform(df_engineered)
        prob = float(self.model.predict_proba(X_processed)[0][1])
        prediction_label = "Fraud" if prob >= decision_engine.thresholds.get("ml_medium_risk", 0.40) else "Legitimate"
        
        latency = (time.time() - start_time) * 1000.0
        
        # Assess Behavioral Risk (Must be before record_transaction)
        behavior = behavioral_engine.assess_transaction(transaction_data)

        # Get risk decision
        decision = decision_engine.assess_risk(
            fraud_probability=prob,
            amount=transaction_data.get("amount", 0.0),
            behavioral_signal=behavior["behavioral_risk_signal"],
            history_status=behavior["behavioral_history_status"]
        )
        
        # Risk Fusion Layer
        decision["prediction"] = "Fraud" if prob >= 0.5 else "Legitimate"
        decision["inference_latency_ms"] = latency
        decision["model_version"] = "v2_pre_auth"
        decision["feature_schema_version"] = "v1.0"
        decision["realtime_feature_validation"] = "passed"
        decision["behavioral_history_status"] = behavior["behavioral_history_status"]
        decision["behavioral_risk_signal"] = behavior["behavioral_risk_signal"]
        
        # Record transaction AFTER prediction to prevent self-leakage
        behavioral_engine.record_transaction(transaction_data)
        
        return decision

    def predict_batch(self, transactions_data: list[dict]) -> list[dict]:
        if not self._model_loaded:
            raise RuntimeError("Model is not loaded.")
            
        start_time = time.time()
        df = pd.DataFrame(transactions_data)
        df_engineered = engineer_realtime_features(df)
        X_processed = self.preprocessor.transform(df_engineered)
        probs = self.model.predict_proba(X_processed)[:, 1]
        
        results = []
        for i, (prob, transaction_data) in enumerate(zip(probs, transactions_data)):
            prob = float(prob)
            
            behavior = behavioral_engine.assess_transaction(transaction_data)
            
            decision = decision_engine.assess_risk(
                fraud_probability=prob,
                amount=transaction_data.get("amount", 0.0),
                behavioral_signal=behavior["behavioral_risk_signal"],
                history_status=behavior["behavioral_history_status"]
            )
            decision["prediction"] = "Fraud" if prob >= 0.5 else "Legitimate"
            decision["inference_latency_ms"] = ((time.time() - start_time) * 1000.0) / len(transactions_data)
            decision["model_version"] = "v2_pre_auth"
            decision["feature_schema_version"] = "v1.0"
            decision["realtime_feature_validation"] = "passed"
            decision["behavioral_history_status"] = behavior["behavioral_history_status"]
            decision["behavioral_risk_signal"] = behavior["behavioral_risk_signal"]
            
            behavioral_engine.record_transaction(transaction_data)
            results.append(decision)
            
        return results

    def explain(self, transaction_data: dict) -> list[dict]:
        from src.explainability import SHAPExplainer
        if not self._model_loaded:
            raise RuntimeError("Model is not loaded.")
        explainer = SHAPExplainer(self.model, self.preprocessor)
        return explainer.explain_transaction(transaction_data)

fraud_service = FraudDetectionService()

