from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from api.schemas import TransactionRequest, TransactionResponse
from api.services import fraud_service
from database.database import get_db
from database.models import TransactionAuditLog

router = APIRouter()


@router.post("/predict", response_model=TransactionResponse)
def predict_fraud(transaction: TransactionRequest, db: Session = Depends(get_db)):
    # Return 503 if model has not been trained/loaded yet
    if not fraud_service.is_ready():
        raise HTTPException(
            status_code=503,
            detail=(
                "Model not loaded. Train the model by running notebooks 05–10 "
                "and ensure artifacts exist in the models/ directory."
            ),
        )

    try:
        # Convert Pydantic schema to standard dictionary
        data = transaction.model_dump()

        # Get prediction
        result = fraud_service.predict(data)

        # Create Audit Log Entry
        audit_entry = TransactionAuditLog(
            step=data["step"],
            type=data["type"],
            amount=data["amount"],
            oldbalanceOrg=data["oldbalanceOrg"],
            newbalanceOrig=data["newbalanceOrig"],
            oldbalanceDest=data["oldbalanceDest"],
            newbalanceDest=data["newbalanceDest"],
            fraud_probability=result["fraud_probability"],
            risk_level=result["risk_level"],
            is_fraud=result["is_fraud"],
        )
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)

        # Attach audit ID to response
        result["audit_id"] = audit_entry.id

        return TransactionResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
