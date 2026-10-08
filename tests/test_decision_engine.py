from src.decision_engine import decision_engine

def test_decision_engine_high_risk_ml():
    result = decision_engine.assess_risk(
        fraud_probability=0.99,
        amount=100.0,
        behavioral_signal=0.0,
        history_status="NONE"
    )
    assert result["risk_level"] == "HIGH"
    assert result["recommended_action"] == "BLOCK"
    assert result["decision_policy"] == "R1_ML_CERTAIN_FRAUD"

def test_decision_engine_behavioral_anomaly():
    result = decision_engine.assess_risk(
        fraud_probability=0.40,
        amount=100.0,
        behavioral_signal=0.8,
        history_status="SUFFICIENT"
    )
    assert result["risk_level"] == "HIGH"
    assert result["recommended_action"] == "BLOCK"
    assert result["decision_policy"] == "R2_BEHAVIORAL_ANOMALY"

def test_decision_engine_high_value_uncertain():
    result = decision_engine.assess_risk(
        fraud_probability=0.40,
        amount=200000.0,
        behavioral_signal=0.0,
        history_status="NONE"
    )
    assert result["risk_level"] == "MEDIUM"
    assert result["recommended_action"] == "VERIFY"
    assert result["decision_policy"] == "R3_HIGH_VALUE_UNCERTAIN"

def test_decision_engine_medium_risk():
    result = decision_engine.assess_risk(
        fraud_probability=0.50,
        amount=100.0,
        behavioral_signal=0.0,
        history_status="NONE"
    )
    assert result["risk_level"] == "MEDIUM"
    assert result["recommended_action"] == "VERIFY"
    assert result["decision_policy"] == "R4_MEDIUM_RISK"

def test_decision_engine_low_risk():
    result = decision_engine.assess_risk(
        fraud_probability=0.10,
        amount=50.0,
        behavioral_signal=0.0,
        history_status="LIMITED"
    )
    assert result["risk_level"] == "LOW"
    assert result["recommended_action"] == "APPROVE"
    assert result["decision_policy"] == "R5_NOMINAL"
    assert result["decision_confidence"] == "MEDIUM_CONFIDENCE"
