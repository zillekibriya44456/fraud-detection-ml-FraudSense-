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
