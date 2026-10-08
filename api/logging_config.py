"""
Structured JSON Logging for Production.
Replaces default uvicorn plaintext logs with JSON-structured logs
compatible with Datadog, Grafana Loki, AWS CloudWatch, and GCP Cloud Logging.
"""
import json
import logging
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import fastapi
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class JsonFormatter(logging.Formatter):
    """Emit logs as single-line JSON objects."""

    LEVEL_MAP = {
        logging.DEBUG: "DEBUG",
        logging.INFO: "INFO",
        logging.WARNING: "WARNING",
        logging.ERROR: "ERROR",
        logging.CRITICAL: "CRITICAL",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": self.LEVEL_MAP.get(record.levelno, "UNKNOWN"),
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        # Attach any extra fields
        for key, val in record.__dict__.items():
            if key not in (
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "message"
            ):
                try:
                    json.dumps(val)  # Only attach JSON-serializable extras
                    payload[key] = val
                except (TypeError, ValueError):
                    pass
        return json.dumps(payload, default=str)


def configure_logging(log_level: str = "INFO", json_logs: bool = True) -> None:
    """Configure root logging for production JSON output."""
    handler = logging.StreamHandler(sys.stdout)
    if json_logs:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)-8s %(name)s - %(message)s"
        ))
    
    root = logging.getLogger()
    root.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    root.handlers.clear()
    root.addHandler(handler)

    # Suppress noisy uvicorn access logs (we handle request logging ourselves)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Structured request/response logging middleware.
    Logs every request as a JSON object with latency, status, request_id, and client IP.
    """
    def __init__(self, app: fastapi.FastAPI, app_name: str = "fraudsense-ai"):
        super().__init__(app)
        self.app_name = app_name
        self.logger = logging.getLogger(f"{app_name}.access")

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
        
        start_ns = time.perf_counter_ns()
        response: Response = await call_next(request)
        duration_ms = (time.perf_counter_ns() - start_ns) / 1_000_000

        # Attach headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"

        log_level = logging.WARNING if response.status_code >= 400 else logging.INFO
        self.logger.log(
            log_level,
            "request_completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query": str(request.url.query),
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "client_ip": client_ip,
                "user_agent": request.headers.get("User-Agent", ""),
            }
        )
        return response
