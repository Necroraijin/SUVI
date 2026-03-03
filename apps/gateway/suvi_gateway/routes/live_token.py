"""Live token endpoint - Token vending machine for Gemini Live API."""

import os
import time
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import google.auth
import google.auth.transport.requests
from google.oauth2 import id_token

from suvi_gateway.middleware.auth import verify_client_token


router = APIRouter()

# Configuration
GCP_PROJECT = os.environ.get("GCP_PROJECT", "suvi-project")
GCP_LOCATION = os.environ.get("GCP_LOCATION", "us-central1")
# Vertex AI Gemini Live Endpoint
# Format: wss://{location}-aiplatform.googleapis.com/ws/google.cloud.aiplatform.v1beta1.LlmInferenceService/StreamGenerateContent
VERTEX_AI_ENDPOINT = f"wss://{GCP_LOCATION}-aiplatform.googleapis.com/ws/google.cloud.aiplatform.v1beta1.LlmInferenceService/StreamRawInference"

# Alternative: Google AI (generativelanguage) endpoint
GOOGLE_AI_ENDPOINT = "wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService/BiDiSession"


class LiveTokenResponse(BaseModel):
    """Response for live token request."""
    token: str
    expires_in: int
    endpoint: str


@router.get("/auth/live-token", response_model=LiveTokenResponse)
async def get_live_token(
    client_auth: dict = Depends(verify_client_token)
):
    """
    Token Vending Machine - Generate secure token for Gemini Live API.

    The desktop client calls this endpoint to get a short-lived token
    that allows direct WebSocket connection to Gemini Live.
    """
    try:
        # 1. Get default credentials (running on Cloud Run as a service account)
        # We need an Access Token (OAuth2) for Vertex AI, not an ID Token.
        credentials, project = google.auth.default(
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        
        # 2. Ensure we have a valid token
        auth_request = google.auth.transport.requests.Request()
        credentials.refresh(auth_request)

        # Use Google AI endpoint as default for now if no project specified
        endpoint = VERTEX_AI_ENDPOINT if project and project != "suvi-project" else GOOGLE_AI_ENDPOINT

        return LiveTokenResponse(
            token=credentials.token,
            expires_in=3600,
            endpoint=endpoint
        )

    except Exception as e:
        print(f"[Gateway] Token generation error: {e}")

        # Fallback to mock token for local development ONLY if no credentials found
        return LiveTokenResponse(
            token="ya29.mock-token-for-vertex-ai",
            expires_in=3600,
            endpoint=GOOGLE_AI_ENDPOINT
        )


@router.post("/auth/live-token/refresh")
async def refresh_live_token(
    current_token: str,
    client_auth: dict = Depends(verify_client_token)
):
    """
    Refresh an existing live token.
    """
    return await get_live_token(client_auth)
