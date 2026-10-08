"""
JWT Authentication & Rate Limiting for FraudSense AI
Production-grade security layer with:
  - JWT Bearer token authentication
  - API Key fallback for service-to-service
  - Sliding window rate limiting (in-memory for single node, Redis for multi-node)
"""
from __future__ import annotations

import secrets
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.settings import settings

# ─── JWT ─────────────────────────────────────────────────────────────────────
try:
    import jwt as pyjwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

JWT_ALGORITHM = "HS256"
JWT_SECRET = getattr(settings, "jwt_secret", settings.api_key or "change-me-in-production")
JWT_EXPIRE_MINUTES = int(getattr(settings, "jwt_expire_minutes", 60))

security_scheme = HTTPBearer(auto_error=False)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    if not JWT_AVAILABLE:
        raise RuntimeError("PyJWT is not installed. Run: pip install PyJWT")
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=JWT_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return pyjwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_jwt_token(token: str) -> dict:
    if not JWT_AVAILABLE:
        raise HTTPException(status_code=500, detail="JWT library not installed.")
    try:
        payload = pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except pyjwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ─── RATE LIMITER ─────────────────────────────────────────────────────────────
class SlidingWindowRateLimiter:
    """
    In-memory sliding window rate limiter.
    For multi-node deployments, replace with Redis-backed implementation.
    """
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: dict[str, deque] = defaultdict(deque)

    def is_allowed(self, key: str) -> tuple[bool, int]:
        now = time.time()
        window_start = now - self.window_seconds
        bucket = self._buckets[key]

        # Remove expired timestamps
        while bucket and bucket[0] < window_start:
            bucket.popleft()

        if len(bucket) >= self.max_requests:
            remaining = 0
            return False, remaining

        bucket.append(now)
        return True, self.max_requests - len(bucket)


# Singleton rate limiters
_predict_limiter = SlidingWindowRateLimiter(max_requests=60, window_seconds=60)   # 60 req/min per key
_batch_limiter = SlidingWindowRateLimiter(max_requests=10, window_seconds=60)     # 10 batch/min
_general_limiter = SlidingWindowRateLimiter(max_requests=200, window_seconds=60)  # 200 req/min general


# ─── UNIFIED AUTH DEPENDENCY ──────────────────────────────────────────────────
def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """
    Legacy API Key auth (backward compatible). Used for service-to-service calls.
    Overridden by require_auth for user-facing endpoints.
    """
    if settings.api_key and not (x_api_key and secrets.compare_digest(x_api_key, settings.api_key)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid X-API-Key header required.",
            headers={"WWW-Authenticate": "ApiKey"},
        )


def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    x_api_key: Optional[str] = Header(default=None),
) -> dict:
    """
    Production dual-auth: accepts either a JWT Bearer token OR an API Key.
    Returns the authenticated identity payload.
    """
    # 1. Try JWT Bearer first
    if credentials and credentials.scheme.lower() == "bearer":
        if JWT_AVAILABLE:
            return verify_jwt_token(credentials.credentials)
        # Fall through to API key if JWT not installed

    # 2. Try API Key fallback
    if x_api_key and settings.api_key:
        if secrets.compare_digest(x_api_key, settings.api_key):
            return {"sub": "api_key_user", "role": "service"}
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # 3. No credentials at all - allow in dev, reject in production
    if getattr(settings, "environment", "development") == "production":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Dev mode: unauthenticated access allowed
    return {"sub": "anonymous", "role": "dev"}


def require_predict_ratelimit(x_api_key: Optional[str] = Header(default=None)) -> None:
    """Rate limit the /predict endpoint per API key or IP."""
    key = x_api_key or "anonymous"
    allowed, remaining = _predict_limiter.is_allowed(key)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Max 60 predictions per minute.",
            headers={"Retry-After": "60", "X-RateLimit-Remaining": "0"},
        )


def require_batch_ratelimit(x_api_key: Optional[str] = Header(default=None)) -> None:
    """Rate limit the /predict_batch endpoint."""
    key = x_api_key or "anonymous"
    allowed, remaining = _batch_limiter.is_allowed(key)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Max 10 batch requests per minute.",
            headers={"Retry-After": "60", "X-RateLimit-Remaining": "0"},
        )
