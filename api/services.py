import joblib
import xgboost as xgb
import pandas as pd
import os
import sys
import logging

logger = logging.getLogger(__name__)

# Ensure src modules can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.feature_engineering import engineer_features

# Paths to models
MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../models'))
MODEL_PATH = os.path.join(MODEL_DIR, 'xgboost_fraud_model.json')
PREPROCESSOR_PATH = os.path.join(MODEL_DIR, 'preprocessor.joblib')


class FraudDetectionService:
    def __init__(self):
        self.model = None
        self.preprocessor = None
        self._model_loaded = False
        self.load_artifacts()

    def load_artifacts(self):
        """
        Attempt to load trained model artifacts.
        If artifacts are missing (e.g. during development before training),
        the service initialises in a degraded state rather than crashing.
        """
        if not os.path.exists(MODEL_PATH) or not os.path.exists(PREPROCESSOR_PATH):
            logger.warning(
                "Model artifacts not found at '%s' and '%s'. "
                "The /predict endpoint will return HTTP 503 until a model is trained. "
                "Run the training notebooks (05–10) to produce model artifacts.",
                MODEL_PATH,
                PREPROCESSOR_PATH,
            )
            self._model_loaded = False
            return

        try:
            self.model = xgb.XGBClassifier()
            self.model.load_model(MODEL_PATH)
            self.preprocessor = joblib.load(PREPROCESSOR_PATH)
            self._model_loaded = True
            logger.info("Model artifacts loaded successfully from '%s'.", MODEL_DIR)
        except Exception as exc:
            logger.error("Failed to load model artifacts: %s", exc)
            self._model_loaded = False

    def is_ready(self) -> bool:
        """Returns True only when model and preprocessor are both loaded."""
        return self._model_loaded

    def predict(self, transaction_data: dict) -> dict:
        """
        Run fraud detection inference on a single transaction.
        Raises RuntimeError if model artifacts have not been loaded.
        """
        if not self._model_loaded:
            raise RuntimeError(
                "Model is not loaded. Train and save the model first "
                "(run notebooks 05–10 and ensure artifacts exist in models/)."
            )

        # 1. Convert to DataFrame
        df = pd.DataFrame([transaction_data])

        # 2. Feature Engineering
        df_engineered = engineer_features(df)

        # 3. Preprocessing
        X_processed = self.preprocessor.transform(df_engineered)

        # 4. Predict
        prob = float(self.model.predict_proba(X_processed)[0][1])

        # 5. Risk Assessment
        # NOTE: These thresholds are provisional placeholders.
        # Final thresholds must be determined by experiments in notebooks 05–10.
        if prob > 0.8:
            risk_level = "High"
            is_fraud = True
        elif prob > 0.4:
            risk_level = "Medium"
            is_fraud = False
        else:
            risk_level = "Low"
            is_fraud = False

        return {
            "fraud_probability": prob,
            "risk_level": risk_level,
            "is_fraud": is_fraud,
        }


# Instantiate a global service to be used by the router
fraud_service = FraudDetectionService()

