from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from api.schemas import TransactionRequest, TransactionResponse, TransactionBatchRequest, TransactionBatchResponse, ExplainResponse
from api.security import require_api_key
from api.services import fraud_service
from database.database import get_db
from database.models import TransactionAuditLog

router = APIRouter()


@router.post("/predict", response_model=TransactionResponse, dependencies=[Depends(require_api_key)])
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
    except Exception:
        import logging
        logging.exception("Prediction failed")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/predict_batch", response_model=TransactionBatchResponse, dependencies=[Depends(require_api_key)])
def predict_fraud_batch(batch_request: TransactionBatchRequest, db: Session = Depends(get_db)):
    if not fraud_service.is_ready():
        raise HTTPException(status_code=503, detail="Model not loaded.")
        
    try:
        transactions = [t.model_dump() for t in batch_request.transactions]
        predictions = fraud_service.predict_batch(transactions)
        
        audit_entries = []
        
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
    except Exception:
        import logging
        logging.exception("Batch prediction failed")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/explain", response_model=ExplainResponse, dependencies=[Depends(require_api_key)])
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
    except Exception:
        import logging
        logging.exception("Explanation generation failed")
        raise HTTPException(status_code=500, detail="Explanation unavailable")


@router.get("/dashboard/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    """Return database-derived dashboard data; never synthesize activity."""
    total = db.query(func.count(TransactionAuditLog.id)).scalar() or 0
    fraud = db.query(func.count(TransactionAuditLog.id)).filter(TransactionAuditLog.prediction == "Fraud").scalar() or 0
    legitimate = db.query(func.count(TransactionAuditLog.id)).filter(TransactionAuditLog.prediction == "Legitimate").scalar() or 0
    distribution = {
        level: count
        for level, count in db.query(TransactionAuditLog.risk_level, func.count(TransactionAuditLog.id))
        .group_by(TransactionAuditLog.risk_level).all()
        if level
    }

    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=24)
    recent_logs = db.query(TransactionAuditLog).filter(TransactionAuditLog.timestamp >= cutoff).order_by(TransactionAuditLog.timestamp.asc()).all()
    buckets: dict[str, dict[str, int]] = {}
    for log in recent_logs:
        timestamp = log.timestamp or datetime.now(timezone.utc).replace(tzinfo=None)
        key = timestamp.strftime("%H:00")
        bucket = buckets.setdefault(key, {"time": key, "legitimate": 0, "fraud": 0, "suspicious": 0})
        if log.prediction == "Fraud":
            bucket["fraud"] += 1
        elif log.risk_level in {"MEDIUM", "HIGH", "CRITICAL"}:
            bucket["suspicious"] += 1
        else:
            bucket["legitimate"] += 1

    return {
        "transactions_analyzed": total,
        "fraud_detected": fraud,
        "legitimate_transactions": legitimate,
        "fraud_rate": round((fraud / total * 100) if total else 0, 2),
        "risk_distribution": distribution,
        "timeline": list(buckets.values()),
    }
