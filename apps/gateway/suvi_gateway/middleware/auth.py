"""Authentication middleware for SUVI Gateway."""

import os
import time
from typing import Optional
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.auth import id_token
from google.auth.exceptions import GoogleAuthError


security = HTTPBearer(auto_error=False)

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
EXPECTED_CLIENT_TOKEN = os.environ.get("SUVI_CLIENT_TOKEN", "suvi-hackathon-secret-123")


async def verify_client_token(request: Request):
    """
    Verify the client token from the desktop app.
    In production, this would validate a JWT from Google OAuth.
    For development, we accept a simple token header.
    """
    # Check for development token
    client_token = request.headers.get("X-Suvi-Client-Auth")

    if client_token == EXPECTED_CLIENT_TOKEN:
        return {"authenticated": True, "method": "token", "client_id": "desktop"}

    # If no token, raise 401
    if not client_token:
        raise HTTPException(
            status_code=401,
            detail="Missing authentication token"
        )

    raise HTTPException(
        status_code=401,
        detail="Invalid authentication token"
    )


async def verify_google_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Verify Google OAuth ID token.
    Used for user authentication via Google Sign-In.
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization credentials"
        )

    try:
        # Verify the Google ID token
        idinfo = id_token.verify_oauth2_token(
            credentials.credentials,
            Request(),
            GOOGLE_CLIENT_ID
        )

        return {
            "authenticated": True,
            "method": "google_oauth",
            "user_id": idinfo.get("sub"),
            "email": idinfo.get("email"),
            "name": idinfo.get("name")
        }

    except GoogleAuthError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid Google token: {str(e)}"
        )


async def get_current_user(
    request: Request,
    google_auth: Optional[dict] = Depends(verify_google_token),
    token_auth: Optional[dict] = Depends(verify_client_token)
) -> dict:
    """
    Get current authenticated user.
    Tries Google OAuth first, falls back to token auth.
    """
    if google_auth:
        return google_auth
    if token_auth:
        return token_auth

    raise HTTPException(
        status_code=401,
        detail="Not authenticated"
    )


class APIKeyValidator:
    """Validate API keys for service-to-service authentication."""

    @staticmethod
    def validate_api_key(request: Request) -> bool:
        """Validate API key from header."""
        api_key = request.headers.get("X-API-Key")
        expected_key = os.environ.get("SUVI_API_KEY", "")

        if not expected_key:
            return True  # Skip validation if no key configured

        return api_key == expected_key
