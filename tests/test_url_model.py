import os
import json
import joblib
import pytest
from src.risk_engine import risk_engine

MODEL_DIR = "models/url_phishing"

def test_url_artifacts_exist():
    assert os.path.exists(os.path.join(MODEL_DIR, "model.joblib")), "model.joblib missing"
    assert os.path.exists(os.path.join(MODEL_DIR, "preprocessor.joblib")), "preprocessor.joblib missing"
    assert os.path.exists(os.path.join(MODEL_DIR, "feature_schema.json")), "feature_schema.json missing"
    assert os.path.exists(os.path.join(MODEL_DIR, "threshold.json")), "threshold.json missing"
    assert os.path.exists(os.path.join(MODEL_DIR, "metrics.json")), "metrics.json missing"
    assert os.path.exists(os.path.join(MODEL_DIR, "metadata.json")), "metadata.json missing"

def test_url_artifacts_loadable():
    model = joblib.load(os.path.join(MODEL_DIR, "model.joblib"))
    preprocessor = joblib.load(os.path.join(MODEL_DIR, "preprocessor.joblib"))
    assert hasattr(model, "predict_proba"), "Model must implement predict_proba"
    assert hasattr(preprocessor, "transform"), "Preprocessor must implement transform"

def test_url_risk_engine_from_raw_url():
    risk_engine.load_models()
    assert risk_engine.is_domain_available("url_phishing"), "url_phishing must be available"
    
    # Test typical phishing-like URL with raw IP and long obfuscated query
    phish_payload = {
        "url": "http://192.168.1.50/login/bank_verification?user=admin&token=xyz%20%20123"
    }
    result = risk_engine.predict("url_phishing", phish_payload)
    
    assert result["domain"] == "URL_PHISHING"
    assert result["model"] == "url_phishing_detector"
    assert result["prediction"] in [0, 1]
    assert result["label"] in ["LEGITIMATE", "PHISHING"]
    assert 0.0 <= result["fraud_probability"] <= 1.0
    assert 0 <= result["risk_score"] <= 100
    assert result["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert isinstance(result["explanations"], list)

def test_url_risk_engine_from_features():
    # Test prediction directly from dictionary of numeric features
    feature_payload = {
        "URLSimilarityIndex": 100,
        "NoOfExternalRef": 5,
        "LineOfCode": 120,
        "NoOfSelfRef": 10,
        "IsHTTPS": 1,
        "Bank": 0,
        "Pay": 0
    }
    result = risk_engine.predict("url_phishing", feature_payload)
    assert 0.0 <= result["fraud_probability"] <= 1.0
    assert 0 <= result["risk_score"] <= 100

def test_url_metadata_content():
    with open(os.path.join(MODEL_DIR, "metadata.json"), "r") as f:
        meta = json.load(f)
    assert meta["domain"] == "URL_PHISHING"
    assert meta["model_name"] == "url_phishing_detector"
    assert meta["test_metrics"]["accuracy"] > 0.95
    assert meta["test_metrics"]["f1_score"] > 0.95
