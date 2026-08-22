from pydantic import BaseModel, Field
from typing import List, Optional

class TransactionRequest(BaseModel):
    transaction_id: str = Field(default="TX_000000", description="Unique transaction ID")
    channel: str = Field(default="GENERIC", description="UPI, CREDIT_CARD, NET_BANKING")
    step: int = Field(..., description="Maps a unit of time. 1 step is 1 hour.")
    type: str = Field(..., description="Transaction type (e.g. TRANSFER, PAYMENT)")
    amount: float = Field(..., description="Amount of the transaction in local currency")
    oldbalanceOrg: float = Field(..., description="Initial sender balance before the transaction")
    oldbalanceDest: float = Field(..., description="Initial recipient balance before the transaction")
    nameOrig: Optional[str] = Field(None, description="Sender Identifier")
    nameDest: Optional[str] = Field(None, description="Recipient Identifier")
    
    # We no longer accept newbalanceOrig and newbalanceDest as they are post-transaction features.
    # To not break batch processing from CSVs that contain it, we can allow them as Optional.
    newbalanceOrig: Optional[float] = None
    newbalanceDest: Optional[float] = None

class TransactionResponse(BaseModel):
    prediction: str = Field(..., description="Fraud or Legitimate")
    fraud_probability: float = Field(..., description="Probability of fraud (0.0 to 1.0)")
    risk_level: str = Field(..., description="LOW, MEDIUM, HIGH")
    recommended_action: str = Field(..., description="APPROVE, VERIFY, BLOCK")
    decision_policy: str = Field(..., description="Policy ID that triggered this decision")
    decision_confidence: str = Field(default="LIMITED_CONTEXT", description="HIGH_CONFIDENCE, MEDIUM_CONFIDENCE, LIMITED_CONTEXT")
    policy_version: str = Field(default="v1.0", description="Version of the risk policy")
    decision_reasons: List[str] = Field(default_factory=list, description="Explanations for the decision")
    model_version: str = Field(default="v2_pre_auth", description="Version of the active ML model")
    inference_latency_ms: float = Field(..., description="Latency of the prediction in milliseconds")
    audit_id: Optional[int] = Field(None, description="The ID of the database audit log")
    case_id: Optional[str] = Field(None, description="The ID of the generated Fraud Case (if any)")
    feature_schema_version: str = Field(default="v1.0", description="Version of the permitted feature schema")
    realtime_feature_validation: str = Field(default="passed", description="Status of the leakage guard validation")
    behavioral_history_status: str = Field(default="NONE", description="NONE, LIMITED, SUFFICIENT")
    behavioral_risk_signal: float = Field(default=0.0, description="Heuristic anomaly score")

class TransactionBatchRequest(BaseModel):
    transactions: List[TransactionRequest]

class TransactionBatchResponse(BaseModel):
    results: List[TransactionResponse]
    total_processed: int

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

class VerifyRequest(BaseModel):
    otp: str = Field(..., description="One-Time Password for Verification")

class CaseStatusUpdate(BaseModel):
    status: str = Field(..., description="OPEN, UNDER_REVIEW, RESOLVED")
    resolution: Optional[str] = Field(None, description="CONFIRMED_FRAUD, FALSE_POSITIVE, VERIFIED_LEGITIMATE")
    notes: Optional[str] = Field(None, description="Analyst notes")
    analyst_id: str = Field("system", description="Analyst making the change")

class CaseHistoryResponse(BaseModel):
    id: int
    case_id: str
    timestamp: datetime
    action: str
    previous_status: Optional[str]
    new_status: Optional[str]
    analyst_id: str
    notes: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)

class CaseResponse(BaseModel):
    id: str
    transaction_id: str
    audit_log_id: int
    severity: str
    status: str
    resolution: Optional[str]
    analyst_notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    fraud_probability: float
    decision: str
    decision_confidence: str
    history: Optional[List[CaseHistoryResponse]] = []
    
    model_config = ConfigDict(from_attributes=True)


class FeatureImpact(BaseModel):
    feature: str
    impact: float

class ExplainResponse(BaseModel):
    transaction_id: str = Field(default="TX_000")
    top_factors: List[FeatureImpact]
