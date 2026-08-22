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
        result = fraud_service.predict(data)

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
        
        # Fraud Alert generation
        from database.models import FraudAlert
        if result["risk_level"] == "HIGH":
            alert = FraudAlert(
                transaction_id=data.get("transaction_id", "TX_000"),
                audit_log_id=audit_entry.id,
                risk_level=result["risk_level"],
                fraud_probability=result["fraud_probability"],
                recommended_action=result["recommended_action"],
                model_version=result["model_version"]
            )
            db.add(alert)
            db.commit()

        result["audit_id"] = audit_entry.id
        return TransactionResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        
        for entry, data, result in zip(audit_entries, transactions, predictions):
            db.refresh(entry)
            result["audit_id"] = entry.id
            if result["risk_level"] == "HIGH":
                alerts.append(FraudAlert(
                    transaction_id=data.get("transaction_id", "TX_000"),
                    audit_log_id=entry.id, risk_level=result["risk_level"],
                    fraud_probability=result["fraud_probability"],
                    recommended_action=result["recommended_action"],
                    model_version=result["model_version"]
                ))
        
        if alerts:
            db.add_all(alerts)
            db.commit()
            
        return TransactionBatchResponse(results=predictions, total_processed=len(predictions))
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
