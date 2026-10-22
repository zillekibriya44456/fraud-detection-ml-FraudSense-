from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from api.case_routes import router as case_router
from api.monitoring_routes import router as monitoring_router
from api.intelligence_routes import router as intelligence_router
from api.upload_routes import router as upload_router
from database import models
from database.database import engine
from api.services import fraud_service
import logging
import time
import uuid

from src.settings import settings

logger = logging.getLogger(__name__)

# Initialize the SQLite Database Tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="FraudSense AI", description="Autonomous Financial Intelligence & Fraud Prevention API")

# Allow the React dev server (port 5173) and production frontend.
# Note: allow_origin_regex handles wildcard subdomain patterns (e.g. *.vercel.app)
# since CORSMiddleware does not support glob wildcards in allow_origins.
_exact_origins = [o for o in settings.cors_origins if "*" not in o]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_exact_origins,
    allow_origin_regex=r"https://[a-zA-Z0-9\-]+\.vercel\.app",
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key", "X-Request-ID"],
)

@app.middleware("http")
async def add_security_headers_and_request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Cache-Control"] = "no-store"
    logger.info("request_completed method=%s path=%s status=%s duration_ms=%.2f request_id=%s", request.method, request.url.path, response.status_code, (time.perf_counter() - started) * 1000, request_id)
    return response

from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": jsonable_encoder(exc.errors())}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception path=%s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error. Please contact support."}
    )

app.include_router(router)
app.include_router(case_router)
app.include_router(monitoring_router)
app.include_router(intelligence_router)
app.include_router(upload_router)

@app.get("/")
def read_root():
    return {"service": "FraudSense AI", "environment": settings.environment}

@app.get("/health")
def health_check():
    return {"status": "healthy", "environment": settings.environment}

@app.get("/readiness")
def readiness_check():
    if fraud_service.is_ready():
        return {"status": "ready", "model_loaded": True}
    return JSONResponse(status_code=503, content={"status": "not_ready", "model_loaded": False})
