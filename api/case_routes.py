from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from database.database import get_db
from database.models import FraudCase, CaseHistory
from api.schemas import CaseResponse, CaseStatusUpdate
from api.security import require_api_key

router = APIRouter(prefix="/cases", tags=["Case Management"])

@router.get("", response_model=List[CaseResponse], dependencies=[Depends(require_api_key)])
@router.get("/", response_model=List[CaseResponse], dependencies=[Depends(require_api_key)], include_in_schema=False)
def get_cases(status: str = None, severity: str = None, db: Session = Depends(get_db)):
    query = db.query(FraudCase)
    if status:
        query = query.filter(FraudCase.status == status)
    if severity:
        query = query.filter(FraudCase.severity == severity)
    
    cases = query.order_by(FraudCase.created_at.desc()).limit(100).all()
    return cases

@router.get("/{case_id}", response_model=CaseResponse, dependencies=[Depends(require_api_key)])
def get_case(case_id: str, db: Session = Depends(get_db)):
    case = db.query(FraudCase).filter(FraudCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    history = db.query(CaseHistory).filter(CaseHistory.case_id == case_id).order_by(CaseHistory.timestamp.asc()).all()
    
    case_resp = CaseResponse.model_validate(case)
    case_resp.history = history
    return case_resp

@router.patch("/{case_id}/status", response_model=CaseResponse, dependencies=[Depends(require_api_key)])
def update_case_status(case_id: str, update: CaseStatusUpdate, db: Session = Depends(get_db)):
    case = db.query(FraudCase).filter(FraudCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    valid_transitions = {
        "OPEN": ["UNDER_REVIEW"],
        "UNDER_REVIEW": ["OPEN", "RESOLVED"],
        "RESOLVED": ["UNDER_REVIEW"] # Re-open
    }
    
    if update.status not in ["OPEN", "UNDER_REVIEW", "RESOLVED"]:
        raise HTTPException(status_code=400, detail="Invalid status")
        
    if update.status != case.status and update.status not in valid_transitions.get(case.status, []):
        raise HTTPException(status_code=400, detail=f"Invalid transition from {case.status} to {update.status}")
        
    if update.status == "RESOLVED" and not update.resolution:
        raise HTTPException(status_code=400, detail="Resolution required when resolving a case")

    prev_status = case.status
    case.status = update.status
    
    if update.resolution:
        case.resolution = update.resolution
    if update.notes:
        if case.analyst_notes:
            case.analyst_notes += f"\n[{update.analyst_id}]: {update.notes}"
        else:
            case.analyst_notes = f"[{update.analyst_id}]: {update.notes}"

    history_entry = CaseHistory(
        case_id=case.id,
        action="STATUS_CHANGED" if prev_status != update.status else "NOTE_ADDED",
        previous_status=prev_status,
        new_status=update.status,
        analyst_id=update.analyst_id,
        notes=update.notes
    )
    
    db.add(history_entry)
    db.commit()
    db.refresh(case)
    
    history = db.query(CaseHistory).filter(CaseHistory.case_id == case_id).order_by(CaseHistory.timestamp.asc()).all()
    case_resp = CaseResponse.model_validate(case)
    case_resp.history = history
    
    return case_resp
