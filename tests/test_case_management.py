import pytest
from fastapi.testclient import TestClient
from api.main import app
from database.database import Base, engine, get_db
from sqlalchemy.orm import sessionmaker

# Use a test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_case_management.db"
engine_test = sessionmaker(autocommit=False, autoflush=False, bind=engine)

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

from unittest.mock import patch

def test_case_creation_on_block(setup_db):
    payload = {
        "transaction_id": "TX_TEST_BLOCK_01",
        "step": 1, "type": "TRANSFER", "amount": 200000.0,
        "oldbalanceOrg": 250000.0, "newbalanceOrig": 50000.0,
        "oldbalanceDest": 0.0, "newbalanceDest": 0.0,
        "nameOrig": "C123", "nameDest": "C456"
    }
    
    with patch("api.services.fraud_service.model.predict_proba") as mock_predict:
        import numpy as np
        # Force a high probability
        mock_predict.return_value = np.array([[0.05, 0.95]])
        
        response = client.post("/predict", json=payload)
        assert response.status_code == 200
    data = response.json()
    
    assert data["recommended_action"] in ["BLOCK", "VERIFY"] # Context engine will trigger one of these
    assert "case_id" in data
    assert data["case_id"] is not None
    
    case_id = data["case_id"]
    
    # Fetch case
    case_resp = client.get(f"/cases/{case_id}")
    assert case_resp.status_code == 200
    case_data = case_resp.json()
    
    assert case_data["transaction_id"] == "TX_TEST_BLOCK_01"
    assert case_data["status"] == "OPEN"

def test_case_deduplication(setup_db):
    payload = {
        "transaction_id": "TX_TEST_DEDUP_01",
        "step": 1, "type": "TRANSFER", "amount": 200000.0,
        "oldbalanceOrg": 250000.0, "newbalanceOrig": 50000.0,
        "oldbalanceDest": 0.0, "newbalanceDest": 0.0,
        "nameOrig": "C123", "nameDest": "C456"
    }
    
    with patch("api.services.fraud_service.model.predict_proba") as mock_predict:
        import numpy as np
        mock_predict.return_value = np.array([[0.05, 0.95]])
        
        response1 = client.post("/predict", json=payload)
        case_id_1 = response1.json().get("case_id")
        
        response2 = client.post("/predict", json=payload)
        case_id_2 = response2.json().get("case_id")
        
        assert case_id_1 == case_id_2 # Should not create a new case for the same TX_ID

def test_case_status_transition(setup_db):
    # Fetch all cases
    cases_resp = client.get("/cases/")
    cases = cases_resp.json()
    case_id = cases[0]["id"]
    
    update_payload = {
        "status": "UNDER_REVIEW",
        "analyst_id": "TEST_ANALYST",
        "notes": "Starting review"
    }
    
    patch_resp = client.patch(f"/cases/{case_id}/status", json=update_payload)
    assert patch_resp.status_code == 200
    updated_case = patch_resp.json()
    
    assert updated_case["status"] == "UNDER_REVIEW"
    assert "TEST_ANALYST" in updated_case["analyst_notes"]
    
    # Resolve
    resolve_payload = {
        "status": "RESOLVED",
        "resolution": "CONFIRMED_FRAUD",
        "analyst_id": "TEST_ANALYST"
    }
    resolve_resp = client.patch(f"/cases/{case_id}/status", json=resolve_payload)
    assert resolve_resp.status_code == 200
    assert resolve_resp.json()["status"] == "RESOLVED"
    assert resolve_resp.json()["resolution"] == "CONFIRMED_FRAUD"

def test_invalid_case_transition(setup_db):
    cases_resp = client.get("/cases/")
    case_id = cases_resp.json()[0]["id"]
    
    # Trying to jump from RESOLVED to OPEN is invalid
    update_payload = {
        "status": "OPEN",
        "analyst_id": "TEST_ANALYST"
    }
    
    patch_resp = client.patch(f"/cases/{case_id}/status", json=update_payload)
    assert patch_resp.status_code == 400
    assert "Invalid transition" in patch_resp.json()["detail"]
