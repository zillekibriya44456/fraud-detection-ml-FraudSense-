import pytest
from src.behavioral.engine import BehavioralEngine

def test_cold_start_transaction():
    engine = BehavioralEngine()
    tx = {
        "nameOrig": "C123",
        "nameDest": "M456",
        "amount": 1000.0
    }
    
    # Assess first (should be cold start)
    features = engine.assess_transaction(tx)
    assert features["behavioral_history_status"] == "NONE"
    assert features["sender_transaction_count_recent"] == 0
    assert features["recipient_transaction_count_recent"] == 0
    assert features["is_new_recipient"] is True
    
    # Record transaction
    engine.record_transaction(tx)
    
    # Assess second transaction from same sender to same recipient
    tx2 = {
        "nameOrig": "C123",
        "nameDest": "M456",
        "amount": 1050.0
    }
    features2 = engine.assess_transaction(tx2)
    assert features2["behavioral_history_status"] == "SUFFICIENT"
    assert features2["sender_transaction_count_recent"] == 1
    assert features2["recipient_transaction_count_recent"] == 1
    assert features2["is_new_recipient"] is False
    assert features2["amount_deviation_score"] > 0

def test_leakage_prevention():
    engine = BehavioralEngine()
    tx = {
        "nameOrig": "C999",
        "nameDest": "M999",
        "amount": 5000.0
    }
    
    features = engine.assess_transaction(tx)
    # The transaction MUST NOT see itself in history
    assert features["sender_transaction_count_recent"] == 0
    
    engine.record_transaction(tx)
    # Now it is in history
    features2 = engine.assess_transaction(tx)
    assert features2["sender_transaction_count_recent"] == 1

def test_velocity_amount_deviation():
    engine = BehavioralEngine()
    # Build history
    for _ in range(5):
        engine.record_transaction({"nameOrig": "C777", "amount": 100.0})
        
    # Sudden massive transaction
    anomalous_tx = {"nameOrig": "C777", "amount": 5000.0}
    features = engine.assess_transaction(anomalous_tx)
    
    assert features["sender_transaction_count_recent"] == 5
    # Deviation should be large and risk signal boosted
    assert features["amount_deviation_score"] > 10.0
    assert features["behavioral_risk_signal"] > 0.4
