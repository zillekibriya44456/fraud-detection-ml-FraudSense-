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
    model_version: str = Field(default="v2_pre_auth", description="Version of the active ML model")
    inference_latency_ms: float = Field(..., description="Latency of the prediction in milliseconds")
    audit_id: Optional[int] = Field(None, description="The ID of the database audit log")

class TransactionBatchRequest(BaseModel):
    transactions: List[TransactionRequest]

class TransactionBatchResponse(BaseModel):
    results: List[TransactionResponse]
    total_processed: int


class FeatureImpact(BaseModel):
    feature: str
    impact: float

class ExplainResponse(BaseModel):
    transaction_id: str = Field(default="TX_000")
    top_factors: List[FeatureImpact]
