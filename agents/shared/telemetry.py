import time
import json

class TelemetryLogger:
    """Logs agent performance, latency, and token usage for the Dashboard."""
    
    def __init__(self, project_id: str = "suvi-core"):
        self.project_id = project_id
        # TODO: Initialize google-cloud-bigquery client here later

    def log_action(self, agent_name: str, action: str, tokens: int, latency_ms: float):
        """Records a single agent action."""
        payload = {
            "timestamp": time.time(),
            "agent": agent_name,
            "action": action,
            "tokens_used": tokens,
            "latency_ms": round(latency_ms, 2)
        }
        
        # Print to terminal for local debugging
        print(f"[Telemetry] 📊 {agent_name} | Action: {action} | Tokens: {tokens} | Latency: {latency_ms:.2f}ms")
        
        # TODO: Stream this payload to BigQuery table `suvi-core.metrics.agent_logs`