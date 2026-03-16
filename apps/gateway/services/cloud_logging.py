import os
from google.cloud import logging

class ActionLogger:
    def __init__(self):
        project_id = os.getenv("GCP_PROJECT_ID")
        self.client = logging.Client(project=project_id)
        self.logger = self.client.logger("suvi-audit-trail")

    def log_event(self, event_name: str, payload: dict):
        """Logs a structured audit event to Google Cloud Logging."""
        self.logger.log_struct(
            {
                "event": event_name,
                **payload
            },
            severity="INFO"
        )
        print(f"Logged to GCP: {event_name}")
