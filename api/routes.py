from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from api.schemas import TransactionRequest, TransactionResponse
from api.services import fraud_service
from database.database import get_db
from database.models import TransactionAuditLog

router = APIRouter()


@router.post("/predict", response_model=TransactionResponse)
def predict_fraud(transaction: TransactionRequest, db: Session = Depends(get_db)):
    if not fraud_service.is_ready():
        raise HTTPException(status_code=503, detail="Model not loaded.")

    try:
        data = transaction.model_dump()
        try:
            result = fraud_service.predict(data)
        except Exception as model_err:
            import logging
            logging.error(f"Model Inference Failed: {str(model_err)}")
            result = {
                "prediction": "SYSTEM_ERROR",
                "fraud_probability": 1.0, # Highest possible risk to be safe
                "risk_level": "UNKNOWN",
                "recommended_action": "REVIEW_REQUIRED",
                "decision_policy": "FAIL_SAFE_POLICY",
                "decision_confidence": "LIMITED_CONTEXT",
                "decision_reasons": ["CRITICAL: Fraud Engine Unavailable. Forcing Review."],
                "model_version": "unknown",
                "inference_latency_ms": 0.0,
                "feature_schema_version": "v1.0",
                "realtime_feature_validation": "failed",
                "behavioral_history_status": "NONE",
                "behavioral_risk_signal": 0.0
            }

        audit_entry = TransactionAuditLog(
            step=data["step"], type=data["type"], amount=data["amount"],
            oldbalanceOrg=data["oldbalanceOrg"], newbalanceOrig=data.get("newbalanceOrig"),
            oldbalanceDest=data["oldbalanceDest"], newbalanceDest=data.get("newbalanceDest"),
            prediction=result["prediction"], fraud_probability=result["fraud_probability"],
            risk_level=result["risk_level"], recommended_action=result["recommended_action"],
            decision_policy=result["decision_policy"], model_version=result["model_version"],
            inference_latency_ms=result["inference_latency_ms"]
        )
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        
        # Phase 5: Automatic Case Creation
        from src.case_manager import case_manager
        case_id = case_manager.evaluate_and_create_case(
            transaction_data=data,
            decision_data=result,
            audit_log_id=audit_entry.id,
            db=db
        )

        result["audit_id"] = audit_entry.id
        result["case_id"] = case_id
        return TransactionResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Critical Transaction Failure: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

from api.schemas import TransactionBatchRequest, TransactionBatchResponse

@router.post("/predict_batch", response_model=TransactionBatchResponse)
def predict_fraud_batch(batch_request: TransactionBatchRequest, db: Session = Depends(get_db)):
    if not fraud_service.is_ready():
        raise HTTPException(status_code=503, detail="Model not loaded.")
        
    try:
        transactions = [t.model_dump() for t in batch_request.transactions]
        predictions = fraud_service.predict_batch(transactions)
        
        audit_entries = []
        alerts = []
        from database.models import FraudAlert
        
        for data, result in zip(transactions, predictions):
            entry = TransactionAuditLog(
                step=data["step"], type=data["type"], amount=data["amount"],
                oldbalanceOrg=data["oldbalanceOrg"], newbalanceOrig=data.get("newbalanceOrig"),
                oldbalanceDest=data["oldbalanceDest"], newbalanceDest=data.get("newbalanceDest"),
                prediction=result["prediction"], fraud_probability=result["fraud_probability"],
                risk_level=result["risk_level"], recommended_action=result["recommended_action"],
                decision_policy=result["decision_policy"], model_version=result["model_version"],
                inference_latency_ms=result["inference_latency_ms"]
            )
            audit_entries.append(entry)
            
        db.add_all(audit_entries)
        db.commit()
        
        from src.case_manager import case_manager
        
        for entry, data, result in zip(audit_entries, transactions, predictions):
            db.refresh(entry)
            result["audit_id"] = entry.id
            
            case_id = case_manager.evaluate_and_create_case(
                transaction_data=data,
                decision_data=result,
                audit_log_id=entry.id,
                db=db
            )
            result["case_id"] = case_id
            
        return TransactionBatchResponse(results=predictions, total_processed=len(predictions))
        
    except HTTPException:
        raise
from api.schemas import ExplainResponse, VerifyRequest
@router.post("/verify_transaction/{transaction_id}")
def verify_transaction(transaction_id: str, request: VerifyRequest):
    """
    Mock endpoint simulating a Step-Up Authentication workflow (OTP).
    If a transaction was routed to VERIFY, the client must successfully call this to APPROVE.
    """
    if request.otp == "123456":
        return {"transaction_id": transaction_id, "verification_status": "SUCCESS", "final_decision": "APPROVE"}
    else:
        return {"transaction_id": transaction_id, "verification_status": "FAILED", "final_decision": "BLOCK"}

from api.schemas import ExplainResponse
@router.post("/explain", response_model=ExplainResponse)
def explain_fraud(transaction: TransactionRequest):
    if not fraud_service.is_ready():
        raise HTTPException(status_code=503, detail="Model not loaded.")
    try:
        data = transaction.model_dump()
        top_factors = fraud_service.explain(data)
        return ExplainResponse(
            transaction_id=data.get("transaction_id", "TX_000"),
            top_factors=top_factors
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
