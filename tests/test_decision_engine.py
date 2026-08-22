import pytest
from src.decision_engine import decision_engine

def test_decision_engine_high_risk():
    result = decision_engine.assess_risk(0.99)
    assert result["risk_level"] == "HIGH"
    assert result["recommended_action"] == "BLOCK"
    assert result["decision_policy"] == "high_risk_threshold_exceeded"

def test_decision_engine_medium_risk():
    result = decision_engine.assess_risk(0.60)
    assert result["risk_level"] == "MEDIUM"
    assert result["recommended_action"] == "VERIFY"

def test_decision_engine_low_risk():
    result = decision_engine.assess_risk(0.10)
    assert result["risk_level"] == "LOW"
    assert result["recommended_action"] == "APPROVE"
