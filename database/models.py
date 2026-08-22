from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from datetime import datetime
from .database import Base

class TransactionAuditLog(Base):
    __tablename__ = "transaction_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
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
    timestamp = Column(DateTime, default=datetime.utcnow)
    transaction_id = Column(String, index=True)
    audit_log_id = Column(Integer)
    risk_level = Column(String)
    fraud_probability = Column(Float)
    recommended_action = Column(String)
    model_version = Column(String)
