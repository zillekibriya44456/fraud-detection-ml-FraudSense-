from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from api.routes import router
from api.case_routes import router as case_router
from api.monitoring_routes import router as monitoring_router
from database import models
from database.database import engine
from api.services import fraud_service
import logging

logger = logging.getLogger(__name__)

# Initialize the SQLite Database Tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="FraudGuard AI", description="Real-time Fraud Detection API")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception on {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error. Please contact support."}
    )

app.include_router(router)
app.include_router(case_router)
app.include_router(monitoring_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to FraudGuard AI API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/readiness")
def readiness_check():
    if fraud_service.is_ready():
        return {"status": "ready", "model_loaded": True}
    return JSONResponse(status_code=503, content={"status": "not_ready", "model_loaded": False})
