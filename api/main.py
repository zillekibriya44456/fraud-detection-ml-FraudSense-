from fastapi import FastAPI
from api.routes import router
from database import models
from database.database import engine

# Initialize the SQLite Database Tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="FraudGuard AI", description="Real-time Fraud Detection API")

app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "Welcome to FraudGuard AI API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
