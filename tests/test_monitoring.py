import pytest
from fastapi.testclient import TestClient
from api.main import app
from database.database import Base, engine, get_db
from database.models import TransactionAuditLog, FraudCase
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch
from datetime import datetime
import json

# Use a test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_monitoring.db"
engine_test = sessionmaker(autocommit=False, autoflush=False, bind=engine)

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    
    # Insert 150 fake logs to bypass INSUFFICIENT_DATA
    for i in range(150):
        log = TransactionAuditLog(
            step=1, type="TRANSFER", amount=1000.0,
            oldbalanceOrg=5000.0, newbalanceOrig=4000.0,
            oldbalanceDest=0.0, newbalanceDest=1000.0,
            prediction="Legitimate", fraud_probability=0.01,
            risk_level="LOW", recommended_action="APPROVE"
        )
        db.add(log)
    
    # Insert 60 resolved cases to bypass INSUFFICIENT_LABELLED_DATA
    for i in range(60):
        case = FraudCase(
            id=f"CASE_{i}",
            transaction_id=f"TX_{i}",
            audit_log_id=i+1,
            severity="HIGH",
            status="RESOLVED",
            resolution="CONFIRMED_FRAUD" if i % 2 == 0 else "FALSE_POSITIVE"
        )
        db.add(case)
        
    db.commit()
    yield
    Base.metadata.drop_all(bind=engine)

def test_monitoring_registry():
    resp = client.get("/monitoring/registry")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ACTIVE"
    assert resp.json()["model_version"] == "v2_pre_auth"

def test_monitoring_performance(setup_db):
    resp = client.get("/monitoring/performance")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert data["sample_size"] == 60
    # 30 confirmed fraud, 30 false positive -> Precision = 0.5
    assert data["metrics"]["precision"] == 0.5

@patch("src.monitoring.drift_analyzer.drift_analyzer.analyze_drift")
def test_retraining_recommendation(mock_drift, setup_db):
    # Mock high drift
    mock_drift.return_value = {
        "status": "SUCCESS",
        "features": [{"severity": "HIGH"}, {"severity": "HIGH"}],
        "prediction_drift": {"severity": "NO_DRIFT"}
    }
    
    resp = client.get("/monitoring/retraining-recommendation")
    assert resp.status_code == 200
    assert resp.json()["recommendation"] == "RETRAINING RECOMMENDED" # Because precision is 0.5 (< 0.8)

    
