"""Quick setup guide for SUVI Google Cloud configuration.

This module provides functions to configure SUVI for Google Cloud.
"""

import os
from typing import Optional


def configure_for_mumbai() -> dict:
    """Configure SUVI for Mumbai region with global access."""
    return {
        "gcp_project": os.environ.get("GCP_PROJECT", ""),
        "gcp_location": "asia-south1",  # Mumbai
        "firestore_location": "asia-south1",
        "pubsub_location": "asia-south1",
        "ai_platform_location": "us-central1",  # Vertex AI not available in Mumbai
    }


def configure_for_global_access() -> dict:
    """Configure SUVI for global accessibility (for judges)."""
    return {
        "enable_cors": True,
        "allowed_origins": ["*"],  # Allow all origins for judges
        "enable_https": True,
        "cloud_run_traffic_split": 100,  # 100% to latest version
    }


def get_deployment_url(project_id: str, region: str = "asia-south1") -> str:
    """Get the deployment URL for the gateway."""
    return f"https://suvi-gateway-{project_id}.{region}.run.app"


def verify_gcp_setup() -> bool:
    """Verify GCP setup is complete."""
    import subprocess

    try:
        # Check gcloud is installed
        result = subprocess.run(
            ["gcloud", "version"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print("ERROR: gcloud CLI not found")
            return False

        # Check project is set
        result = subprocess.run(
            ["gcloud", "config", "get-value", "project"],
            capture_output=True,
            text=True
        )
        if not result.stdout.strip():
            print("ERROR: No GCP project set. Run: gcloud init")
            return False

        print(f"✓ GCP configured for project: {result.stdout.strip()}")
        return True

    except FileNotFoundError:
        print("ERROR: gcloud CLI not installed")
        return False


# Export configuration
MUMBAI_CONFIG = configure_for_mumbai()
GLOBAL_CONFIG = configure_for_global_access()
