from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.database import get_db
from src.monitoring.drift_analyzer import drift_analyzer
from src.monitoring.performance_analyzer import performance_analyzer
from src.monitoring.registry import model_registry

router = APIRouter(prefix="/monitoring", tags=["Model Monitoring"])

@router.get("/drift")
def get_drift_analysis(db: Session = Depends(get_db)):
    return drift_analyzer.analyze_drift(db)

@router.get("/performance")
def get_performance_analysis(db: Session = Depends(get_db)):
    return performance_analyzer.analyze_performance(db)

@router.get("/registry")
def get_model_registry():
    return model_registry.get_active_model()

@router.get("/retraining-recommendation")
def get_retraining_recommendation(db: Session = Depends(get_db)):
    drift = drift_analyzer.analyze_drift(db)
    performance = performance_analyzer.analyze_performance(db)
    
    return model_registry.evaluate_retraining_need(drift, performance)
