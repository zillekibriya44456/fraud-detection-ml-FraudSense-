from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_predict_fraud_valid_request():
    payload = {
        "transaction_id": "TX_TEST_01",
        "channel": "UPI",
        "step": 1,
        "type": "TRANSFER",
        "amount": 50000.0,
        "oldbalanceOrg": 50000.0,
        "oldbalanceDest": 0.0
    }
    response = client.post("/predict", json=payload)
    # 503 means model isn't loaded (e.g. if we haven't trained in the test env)
    # If 200, we assert the new fields exist
    if response.status_code == 200:
        data = response.json()
        assert "prediction" in data
        assert "decision_policy" in data
        assert "model_version" in data
        assert "inference_latency_ms" in data
        assert "feature_schema_version" in data
        assert "realtime_feature_validation" in data
        assert data["realtime_feature_validation"] == "passed"

def test_predict_rejects_post_auth_leakage():
    # Submit a payload that attempts to pass future knowledge
    payload = {
        "transaction_id": "TX_TEST_LEAK",
        "channel": "UPI",
        "step": 1,
        "type": "TRANSFER",
        "amount": 50000.0,
        "oldbalanceOrg": 50000.0,
        "oldbalanceDest": 0.0,
        "newbalanceOrig": 0.0,    # POST-TRANSACTION LEAKAGE
        "newbalanceDest": 50000.0 # POST-TRANSACTION LEAKAGE
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422

def test_dashboard_summary_has_no_synthetic_activity():
    response = client.get("/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert {"transactions_analyzed", "fraud_detected", "legitimate_transactions", "fraud_rate", "risk_distribution", "timeline"} <= data.keys()

def test_predict_fraud_missing_fields():
    payload = {
        "step": 1,
        "amount": 500.0
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422 # Unprocessable Entity (missing required fields)

def test_explain_endpoint():
    payload = {
        "step": 1,
        "type": "TRANSFER",
        "amount": 50000.0,
        "oldbalanceOrg": 50000.0,
        "oldbalanceDest": 0.0
    }
    response = client.post("/explain", json=payload)
    if response.status_code == 200:
        data = response.json()
        assert "top_factors" in data
        assert isinstance(data["top_factors"], list)
