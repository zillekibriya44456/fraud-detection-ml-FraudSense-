from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime, timezone
from .database import Base

class TransactionAuditLog(Base):
    __tablename__ = "transaction_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Input features
    step = Column(Integer)
    type = Column(String)
    amount = Column(Float)
    oldbalanceOrg = Column(Float)
    newbalanceOrig = Column(Float)
    oldbalanceDest = Column(Float)
    newbalanceDest = Column(Float)
    
    # Model Outputs
    prediction = Column(String)
    fraud_probability = Column(Float)
    risk_level = Column(String)
    recommended_action = Column(String)
    decision_policy = Column(String, default="legacy")
    model_version = Column(String, default="legacy")
    inference_latency_ms = Column(Float, default=0.0)

class FraudAlert(Base):
    __tablename__ = "fraud_alerts"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    transaction_id = Column(String, index=True)
    audit_log_id = Column(Integer)
    risk_level = Column(String)
    fraud_probability = Column(Float)
    model_version = Column(String)

class FraudCase(Base):
    __tablename__ = "fraud_cases"

    id = Column(String, primary_key=True, index=True) # e.g., CASE_12345
    transaction_id = Column(String, index=True)
    audit_log_id = Column(Integer)
    severity = Column(String) # CRITICAL, HIGH, MEDIUM, LOW
    status = Column(String, default="OPEN") # OPEN, UNDER_REVIEW, RESOLVED
    resolution = Column(String, nullable=True) # CONFIRMED_FRAUD, FALSE_POSITIVE, VERIFIED_LEGITIMATE
    analyst_notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Context snapshots
    fraud_probability = Column(Float)
    decision = Column(String)
    decision_confidence = Column(String)

class CaseHistory(Base):
    __tablename__ = "case_history"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    action = Column(String) # STATUS_CHANGED, NOTE_ADDED
    previous_status = Column(String, nullable=True)
    new_status = Column(String, nullable=True)
    analyst_id = Column(String, default="system")
    notes = Column(String, nullable=True)
