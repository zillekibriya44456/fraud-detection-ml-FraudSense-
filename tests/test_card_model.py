import os
import json
import joblib
import pytest
from src.risk_engine import risk_engine

MODEL_DIR = "models/card"

def test_card_artifacts_exist():
    assert os.path.exists(os.path.join(MODEL_DIR, "model.joblib")), "model.joblib missing"
    assert os.path.exists(os.path.join(MODEL_DIR, "preprocessor.joblib")), "preprocessor.joblib missing"
    assert os.path.exists(os.path.join(MODEL_DIR, "feature_schema.json")), "feature_schema.json missing"
    assert os.path.exists(os.path.join(MODEL_DIR, "threshold.json")), "threshold.json missing"
    assert os.path.exists(os.path.join(MODEL_DIR, "metrics.json")), "metrics.json missing"
    assert os.path.exists(os.path.join(MODEL_DIR, "metadata.json")), "metadata.json missing"

def test_card_artifacts_loadable():
    model = joblib.load(os.path.join(MODEL_DIR, "model.joblib"))
    preprocessor = joblib.load(os.path.join(MODEL_DIR, "preprocessor.joblib"))
    assert hasattr(model, "predict_proba"), "Model must implement predict_proba"
    assert hasattr(preprocessor, "transform"), "Preprocessor must implement transform"

def test_card_risk_engine_inference():
    # Force reload in case models were cached
    risk_engine.load_models()
    assert risk_engine.is_domain_available("card"), "Card domain should be available in risk_engine"
    
    sample_transaction = {
        "Time": 45000.0,
        "Amount": 149.50,
        "V1": -1.25,
        "V2": 0.85,
        "V3": 1.12,
        "V4": 0.45,
        "V14": -0.85
    }
    
    result = risk_engine.predict("card", sample_transaction)
    
    assert result["domain"] == "CARD"
    assert result["model"] == "credit_card_fraud_detector"
    assert result["prediction"] in [0, 1]
    assert result["label"] in ["LEGITIMATE", "FRAUD"]
    assert 0.0 <= result["fraud_probability"] <= 1.0
    assert 0 <= result["risk_score"] <= 100
    assert result["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert "threshold" in result
    assert isinstance(result["explanations"], list)

def test_card_high_risk_signature():
    # Extreme latent features characteristic of card fraud
    high_risk_payload = {
        "Time": 2000.0,
        "Amount": 1200.0,
        "V14": -7.5,
        "V4": 4.5,
        "V10": -5.2,
        "V12": -6.1
    }
    result = risk_engine.predict("card", high_risk_payload)
    assert result["fraud_probability"] > 0.20
    assert len(result["explanations"]) > 0

def test_card_metadata_content():
    with open(os.path.join(MODEL_DIR, "metadata.json"), "r") as f:
        meta = json.load(f)
    assert meta["domain"] == "CARD"
    assert meta["model_name"] == "credit_card_fraud_detector"
    assert meta["algorithm"] == "XGBoost"
    assert meta["test_metrics"]["pr_auc"] > 0.75
    assert meta["test_metrics"]["roc_auc"] > 0.90
