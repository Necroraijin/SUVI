import time
import json
import os
from typing import Optional
from google.cloud import bigquery
from google.auth.exceptions import DefaultCredentialsError

class TelemetryLogger:
    """Logs agent performance, latency, and token usage for the Dashboard."""
    
    def __init__(self, project_id: Optional[str] = None):
        self.project_id = project_id or os.environ.get("GCP_PROJECT", "suvi-core")
        self.dataset_id = "metrics"
        self.table_id = "agent_logs"
        self.client: Optional[bigquery.Client] = None
        
        try:
            # Initialize BigQuery client if credentials available
            self.client = bigquery.Client(project=self.project_id)
            print(f"[Telemetry] BigQuery client initialized for project: {self.project_id}")
        except (DefaultCredentialsError, Exception) as e:
            print(f"[Telemetry] Running in local/mock mode: {e}")

    def log_action(self, agent_name: str, action: str, tokens: int, latency_ms: float):
        """Records a single agent action and streams it to BigQuery."""
        payload = {
            "timestamp": time.time(),
            "agent": agent_name,
            "action": action,
            "tokens_used": tokens,
            "latency_ms": round(latency_ms, 2)
        }
        
        # Print to terminal for local debugging
        print(f"[Telemetry] 📊 {agent_name} | Action: {action} | Tokens: {tokens} | Latency: {latency_ms:.2f}ms")
        
        if self.client:
            try:
                table_ref = self.client.dataset(self.dataset_id).table(self.table_id)
                errors = self.client.insert_rows_json(table_ref, [payload])
                if errors:
                    print(f"[Telemetry Error] BigQuery insert failed: {errors}")
            except Exception as e:
                print(f"[Telemetry Error] Streaming failed: {e}")
        else:
            # Mock: In local dev, we might write to a local JSON file instead
            self._log_to_local_file(payload)

    def _log_to_local_file(self, payload: dict):
        log_file = "telemetry_local.log"
        try:
            with open(log_file, "a") as f:
                f.write(json.dumps(payload) + "\n")
        except Exception:
            pass
