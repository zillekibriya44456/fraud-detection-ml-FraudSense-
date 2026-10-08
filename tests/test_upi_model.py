import os
import json
import joblib
import pytest
from src.risk_engine import risk_engine

MODEL_DIR = "models/upi"

def test_upi_artifacts_exist():
    assert os.path.exists(os.path.join(MODEL_DIR, "model.joblib")), "model.joblib missing"
    assert os.path.exists(os.path.join(MODEL_DIR, "preprocessor.joblib")), "preprocessor.joblib missing"
    assert os.path.exists(os.path.join(MODEL_DIR, "feature_schema.json")), "feature_schema.json missing"
    assert os.path.exists(os.path.join(MODEL_DIR, "threshold.json")), "threshold.json missing"
    assert os.path.exists(os.path.join(MODEL_DIR, "metrics.json")), "metrics.json missing"
    assert os.path.exists(os.path.join(MODEL_DIR, "metadata.json")), "metadata.json missing"

def test_upi_artifacts_loadable():
    model = joblib.load(os.path.join(MODEL_DIR, "model.joblib"))
    preprocessor = joblib.load(os.path.join(MODEL_DIR, "preprocessor.joblib"))
    assert hasattr(model, "predict_proba"), "Model must implement predict_proba"
    assert hasattr(preprocessor, "transform"), "Preprocessor must implement transform"

def test_upi_risk_engine_inference():
    assert risk_engine.is_domain_available("upi"), "UPI domain should be available in risk_engine"
    
    sample_transaction = {
        "amount (INR)": 2500.0,
        "transaction type": "P2P",
        "merchant_category": "Shopping",
        "sender_age_group": "26-35",
        "receiver_age_group": "18-25",
        "sender_state": "Delhi",
        "sender_bank": "HDFC",
        "receiver_bank": "SBI",
        "device_type": "Android",
        "network_type": "5G",
        "hour_of_day": 14,
        "day_of_week": "Wednesday",
        "is_weekend": 0
    }
    
    result = risk_engine.predict("upi", sample_transaction)
    
    assert result["domain"] == "UPI"
    assert result["model"] == "upi_fraud_detector"
    assert result["prediction"] in [0, 1]
    assert result["label"] in ["LEGITIMATE", "FRAUD"]
    assert 0.0 <= result["fraud_probability"] <= 1.0
    assert 0 <= result["risk_score"] <= 100
    assert result["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert "threshold" in result
    assert isinstance(result["explanations"], list)

def test_upi_missing_fields_defaults():
    # Only providing minimum fields to verify robustness against missing inputs
    sparse_payload = {
        "amount": 150.0
    }
    result = risk_engine.predict("upi", sparse_payload)
    assert 0.0 <= result["fraud_probability"] <= 1.0
    assert 0 <= result["risk_score"] <= 100

def test_upi_metadata_content():
    with open(os.path.join(MODEL_DIR, "metadata.json"), "r") as f:
        meta = json.load(f)
    assert meta["domain"] == "UPI"
    assert meta["model_name"] == "upi_fraud_detector"
    assert "test_metrics" in meta
    assert meta["train_rows"] == 175000
    assert meta["test_rows"] == 37500
