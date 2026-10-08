"""
JWT Token endpoint for FraudSense AI.
Provides /auth/token and /auth/refresh endpoints for production OAuth2-style authentication.
"""
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from api.security import create_access_token, JWT_EXPIRE_MINUTES
from src.settings import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = JWT_EXPIRE_MINUTES * 60


class TokenRequest(BaseModel):
    api_key: str
    client_id: Optional[str] = "default"


@router.post("/token", response_model=TokenResponse, summary="Exchange API key for JWT token")
def get_token(request: TokenRequest) -> TokenResponse:
    """
    Exchange a long-lived API key for a short-lived JWT Bearer token.
    The JWT token should be used in subsequent API requests via the Authorization: Bearer header.
    
    In production, replace this with OAuth2 + Identity Provider (e.g. Okta, Auth0, Keycloak).
    """
    import secrets as _secrets
    if not settings.api_key or not _secrets.compare_digest(request.api_key, settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )
    
    token_data = {
        "sub": request.client_id,
        "role": "analyst",
        "scopes": ["predict", "read", "cases"],
    }
    token = create_access_token(
        data=token_data,
        expires_delta=timedelta(minutes=JWT_EXPIRE_MINUTES),
    )
    return TokenResponse(
        access_token=token,
        expires_in=JWT_EXPIRE_MINUTES * 60,
    )


@router.get("/me", summary="Get current authenticated identity")
def get_me(
    credentials = Depends(__import__("api.security", fromlist=["require_auth"]).require_auth)
) -> dict:
    """Returns the currently authenticated identity from the JWT or API key."""
    return {"identity": credentials}
