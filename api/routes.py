from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy import func, case, or_
from sqlalchemy.orm import Session
from api.schemas import TransactionRequest, TransactionResponse, TransactionBatchRequest, TransactionBatchResponse, ExplainResponse
from api.security import require_api_key
from api.services import fraud_service
from database.database import get_db
from database.models import TransactionAuditLog, FraudCase

router = APIRouter()

# ── Helpers ──────────────────────────────────────────────────────────────────

FRAUD_LABELS = {"FRAUD", "SPAM_SCAM", "PHISHING", "SCAM", "SPAM"}
LEGIT_LABELS  = {"LEGITIMATE", "LICIT", "SAFE", "NOT_FRAUD"}

def _is_fraud(prediction: str | None) -> bool:
    return (prediction or "").upper() in FRAUD_LABELS

def _is_legit(prediction: str | None) -> bool:
    return (prediction or "").upper() in LEGIT_LABELS

def _range_cutoff(range_param: str) -> datetime:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    mapping = {"24h": 24, "7d": 168, "30d": 720}
    return now - timedelta(hours=mapping.get(range_param, 24))

# ── Domain label map ─────────────────────────────────────────────────────────

DOMAIN_LABELS: dict[str, str] = {
    "paysim_fraud_detector":       "PaySim",
    "upi_fraud_detector":          "UPI",
    "bitcoin_fraud_detector":      "Bitcoin",
    "sms_spam_detector":           "SMS Spam",
    "email_phishing_detector":     "Email Phishing",
    "bank_fraud_detector":         "Bank Transfer",
    "url_phishing_detector":       "URL Phishing",
    "credit_card_fraud_detector":  "Credit Card",
}


# ─────────────────────────────────────────────────────────────────────────────
#  PREDICT
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/predict", response_model=TransactionResponse, dependencies=[Depends(require_api_key)])
def predict_fraud(transaction: TransactionRequest, db: Session = Depends(get_db)):
    if not fraud_service.is_ready():
        raise HTTPException(status_code=503, detail="Model not loaded.")

    try:
        data = transaction.model_dump()
        result = fraud_service.predict(data)

        audit_entry = TransactionAuditLog(
            step=int(data.get("step") or 0),
            type=str(data.get("type") or data.get("domain") or "UNKNOWN"),
            amount=float(data.get("amount") or data.get("Amount") or 0.0),
            oldbalanceOrg=float(data.get("oldbalanceOrg") or 0.0),
            newbalanceOrig=data.get("newbalanceOrig"),
            oldbalanceDest=float(data.get("oldbalanceDest") or 0.0),
            newbalanceDest=data.get("newbalanceDest"),
            prediction=result["prediction"],
            fraud_probability=result["fraud_probability"],
            risk_level=result["risk_level"],
            recommended_action=result["recommended_action"],
            decision_policy=result["decision_policy"],
            model_version=result["model_version"],
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


# ─────────────────────────────────────────────────────────────────────────────
#  DASHBOARD — SUMMARY
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/dashboard/summary")
def dashboard_summary(
    range: str = Query("24h", pattern="^(24h|7d|30d)$"),
    db: Session = Depends(get_db),
):
    """Return database-derived dashboard data; never synthesize activity."""
    cutoff = _range_cutoff(range)

    # ── Global counts (all time, for KPI totals) ────────────────────────────
    total_all_time = db.query(func.count(TransactionAuditLog.id)).scalar() or 0

    all_logs = db.query(
        TransactionAuditLog.prediction,
        TransactionAuditLog.amount,
    ).all()

    fraud_count   = sum(1 for r in all_logs if _is_fraud(r.prediction))
    legit_count   = sum(1 for r in all_logs if _is_legit(r.prediction))
    amount_at_risk = sum(
        (r.amount or 0)
        for r in db.query(TransactionAuditLog.amount, TransactionAuditLog.prediction).all()
        if _is_fraud(r.prediction)
    )
    total_amount = sum(
        r.amount or 0
        for r in db.query(TransactionAuditLog.amount).all()
    )

    # ── Confirmed fraud cases ───────────────────────────────────────────────
    confirmed_fraud_cases = (
        db.query(func.count(FraudCase.id))
        .filter(FraudCase.resolution == "CONFIRMED_FRAUD")
        .scalar() or 0
    )
    open_cases = (
        db.query(func.count(FraudCase.id))
        .filter(FraudCase.status == "OPEN")
        .scalar() or 0
    )

    # ── Risk distribution (all time) ────────────────────────────────────────
    risk_rows = (
        db.query(TransactionAuditLog.risk_level, func.count(TransactionAuditLog.id))
        .group_by(TransactionAuditLog.risk_level)
        .all()
    )
    distribution = {level: count for level, count in risk_rows if level}

    # ── Domain breakdown (all time) ─────────────────────────────────────────
    domain_rows = (
        db.query(TransactionAuditLog.model_version, func.count(TransactionAuditLog.id))
        .group_by(TransactionAuditLog.model_version)
        .all()
    )
    domain_breakdown = {
        DOMAIN_LABELS.get(mv, mv): cnt
        for mv, cnt in domain_rows
        if mv
    }

    # ── Avg inference latency ───────────────────────────────────────────────
    avg_latency = (
        db.query(func.avg(TransactionAuditLog.inference_latency_ms)).scalar() or 0.0
    )

    # ── Timeline (within selected range) ────────────────────────────────────
    recent_logs = (
        db.query(TransactionAuditLog)
        .filter(TransactionAuditLog.timestamp >= cutoff)
        .order_by(TransactionAuditLog.timestamp.asc())
        .all()
    )

    # Bucket resolution depends on range
    if range == "24h":
        fmt = "%H:00"
    elif range == "7d":
        fmt = "%a %d"
    else:
        fmt = "%b %d"

    buckets: dict[str, dict] = {}
    for log in recent_logs:
        ts = log.timestamp or datetime.now(timezone.utc).replace(tzinfo=None)
        key = ts.strftime(fmt)
        bucket = buckets.setdefault(key, {
            "time": key, "total": 0,
            "legitimate": 0, "fraud": 0, "suspicious": 0,
        })
        bucket["total"] += 1
        if _is_fraud(log.prediction):
            bucket["fraud"] += 1
        elif log.risk_level in {"HIGH", "CRITICAL"}:
            bucket["suspicious"] += 1
        else:
            bucket["legitimate"] += 1

    return {
        # KPI totals
        "transactions_analyzed": total_all_time,
        "fraud_detected": fraud_count,
        "legitimate_transactions": legit_count,
        "fraud_rate": round((fraud_count / total_all_time * 100) if total_all_time else 0, 2),
        "amount_at_risk": round(amount_at_risk, 2),
        "total_amount_analyzed": round(total_amount, 2),
        # Cases
        "confirmed_fraud_cases": confirmed_fraud_cases,
        "open_cases_count": open_cases,
        # Charts / breakdown
        "risk_distribution": distribution,
        "domain_breakdown": domain_breakdown,
        "avg_inference_latency_ms": round(avg_latency, 2),
        # Timeline
        "timeline": list(buckets.values()),
        "timeline_range": range,
    }


# ─────────────────────────────────────────────────────────────────────────────
#  DASHBOARD — RECENT TRANSACTIONS (paginated)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/dashboard/transactions")
def dashboard_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query("", alias="q"),
    risk: str = Query("", description="Comma-separated risk levels e.g. HIGH,CRITICAL"),
    db: Session = Depends(get_db),
):
    """Paginated recent transactions for the dashboard table."""
    q = db.query(TransactionAuditLog)

    # Risk filter
    if risk:
        levels = [r.strip().upper() for r in risk.split(",") if r.strip()]
        if levels:
            q = q.filter(TransactionAuditLog.risk_level.in_(levels))

    # Search by type / model_version / prediction
    if search:
        pattern = f"%{search}%"
        q = q.filter(
            or_(
                TransactionAuditLog.type.ilike(pattern),
                TransactionAuditLog.model_version.ilike(pattern),
                TransactionAuditLog.prediction.ilike(pattern),
                TransactionAuditLog.recommended_action.ilike(pattern),
            )
        )

    total = q.count()
    rows = (
        q.order_by(TransactionAuditLog.timestamp.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    def _serialize(r: TransactionAuditLog) -> dict:
        return {
            "id":                  r.id,
            "timestamp":           r.timestamp.isoformat() if r.timestamp else None,
            "type":                r.type,
            "model_version":       r.model_version,
            "domain_label":        DOMAIN_LABELS.get(r.model_version or "", r.type or "Unknown"),
            "amount":              r.amount,
            "fraud_probability":   round(r.fraud_probability or 0, 4),
            "risk_level":          r.risk_level,
            "prediction":          r.prediction,
            "recommended_action":  r.recommended_action,
            "decision_policy":     r.decision_policy,
            "inference_latency_ms": r.inference_latency_ms,
        }

    return {
        "page":       page,
        "page_size":  page_size,
        "total":      total,
        "pages":      max(1, (total + page_size - 1) // page_size),
        "results":    [_serialize(r) for r in rows],
    }


# ─────────────────────────────────────────────────────────────────────────────
#  DASHBOARD — RECENT ALERTS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/dashboard/alerts")
def dashboard_alerts(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Return recent high-risk audit records as alert events."""
    rows = (
        db.query(TransactionAuditLog)
        .filter(TransactionAuditLog.risk_level.in_(["HIGH", "CRITICAL"]))
        .order_by(TransactionAuditLog.timestamp.desc())
        .limit(limit)
        .all()
    )

    def _alert(r: TransactionAuditLog) -> dict:
        return {
            "id":             r.id,
            "timestamp":      r.timestamp.isoformat() if r.timestamp else None,
            "type":           r.type,
            "domain_label":   DOMAIN_LABELS.get(r.model_version or "", r.type or "Unknown"),
            "risk_level":     r.risk_level,
            "fraud_probability": round(r.fraud_probability or 0, 4),
            "prediction":     r.prediction,
            "recommended_action": r.recommended_action,
        }

    return {"alerts": [_alert(r) for r in rows], "total": len(rows)}
