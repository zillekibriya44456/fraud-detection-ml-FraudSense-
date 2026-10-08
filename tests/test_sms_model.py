import os
import json
import joblib
import pytest
from src.risk_engine import risk_engine

MODEL_DIR = "models/sms"

def test_sms_artifacts_exist():
    assert os.path.exists(os.path.join(MODEL_DIR, "model.joblib")), "model.joblib missing"
    assert os.path.exists(os.path.join(MODEL_DIR, "preprocessor.joblib")), "preprocessor.joblib missing"
    assert os.path.exists(os.path.join(MODEL_DIR, "feature_schema.json")), "feature_schema.json missing"
    assert os.path.exists(os.path.join(MODEL_DIR, "threshold.json")), "threshold.json missing"
    assert os.path.exists(os.path.join(MODEL_DIR, "metrics.json")), "metrics.json missing"
    assert os.path.exists(os.path.join(MODEL_DIR, "metadata.json")), "metadata.json missing"

def test_sms_artifacts_loadable():
    model = joblib.load(os.path.join(MODEL_DIR, "model.joblib"))
    bundle = joblib.load(os.path.join(MODEL_DIR, "preprocessor.joblib"))
    assert hasattr(model, "predict_proba"), "Model must implement predict_proba"
    assert "vectorizer" in bundle, "Bundle must contain vectorizer"
    assert "scaler" in bundle, "Bundle must contain scaler"

def test_sms_risk_engine_spam_detection():
    risk_engine.load_models()
    assert risk_engine.is_domain_available("sms"), "sms domain must be available"
    
    spam_msg = {
        "text": "WINNER!! Claim your $1000 cash prize immediately by calling 0800123456 now or click https://claim-prize.fake"
    }
    result = risk_engine.predict("sms", spam_msg)
    
    assert result["domain"] == "SMS"
    assert result["model"] == "sms_spam_detector"
    assert result["prediction"] == 1
    assert result["label"] == "SPAM_SCAM"
    assert result["fraud_probability"] > 0.50
    assert result["risk_score"] > 50
    assert result["risk_level"] in ["HIGH", "CRITICAL"]
    assert len(result["explanations"]) > 0

def test_sms_risk_engine_ham_detection():
    ham_msg = {
        "text": "Hey mom, I will be home by 6pm for dinner, see you soon."
    }
    result = risk_engine.predict("sms", ham_msg)
    
    assert result["domain"] == "SMS"
    assert result["prediction"] == 0
    assert result["label"] == "HAM_LEGITIMATE"
    assert result["fraud_probability"] < 0.40
    assert result["risk_score"] < 40

def test_sms_empty_payload_robustness():
    result = risk_engine.predict("sms", {"text": ""})
    assert result["prediction"] == 0
    assert result["risk_score"] == 0

def test_sms_metadata_content():
    with open(os.path.join(MODEL_DIR, "metadata.json"), "r") as f:
        meta = json.load(f)
    assert meta["domain"] == "SMS"
    assert meta["model_name"] == "sms_spam_detector"
    assert meta["test_metrics"]["f1_score"] > 0.90
    assert meta["test_metrics"]["accuracy"] > 0.95
