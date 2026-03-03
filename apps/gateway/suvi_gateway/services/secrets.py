"""Google Cloud Secret Manager integration."""

import os
from typing import Optional
from google.cloud import secretmanager


class SecretManager:
    """Fetches API keys securely from Google Cloud Secret Manager."""

    def __init__(self, project_id: str = None):
        self.project_id = project_id or os.environ.get("GCP_PROJECT", "suvi-project")
        self.client = secretmanager.SecretManagerServiceClient()

    def get_secret(self, secret_id: str, version: str = "latest") -> Optional[str]:
        """
        Get a secret from Google Cloud Secret Manager.

        Args:
            secret_id: The ID of the secret
            version: The version of the secret (default: latest)

        Returns:
            The secret value or None if not found
        """
        try:
            name = f"projects/{self.project_id}/secrets/{secret_id}/versions/{version}"
            response = self.client.access_secret_version(name=name)
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            print(f"[SecretManager] Error fetching secret {secret_id}: {e}")
            return None

    def get_vertex_api_key(self) -> str:
        """Get Vertex AI API key."""
        # First try environment variable
        key = os.environ.get("VERTEX_API_KEY")
        if key:
            return key

        # Then try Secret Manager
        key = self.get_secret("vertex-api-key")
        if key:
            return key

        print("[SecretManager] Warning: VERTEX_API_KEY not found, using mock")
        return "mock-key-123"

    def get_gemini_api_key(self) -> str:
        """Get Gemini API key."""
        key = os.environ.get("GEMINI_API_KEY")
        if key:
            return key

        key = self.get_secret("gemini-api-key")
        if key:
            return key

        return "mock-gemini-key"

    def get_firestore_credentials(self) -> Optional[dict]:
        """Get Firestore credentials."""
        creds_json = self.get_secret("firestore-credentials")
        if creds_json:
            import json
            return json.loads(creds_json)
        return None
