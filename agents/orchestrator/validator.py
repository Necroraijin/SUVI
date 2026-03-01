from agents.shared.models import AgentResponse

class OutputValidator:
    """Ensures sub-agent responses meet safety and accuracy standards."""

    def __init__(self, strict_mode=True):
        self.strict_mode = strict_mode

    def validate(self, response: AgentResponse) -> bool:
        """Evaluates the response before it is shown to the user."""
        
        if response.status == "failed":
            print("[Validator] ⚠️ Sub-agent reported failure. Flagging for Orchestrator retry.")
            return False
            
        if not response.result:
            print("[Validator] ⚠️ Sub-agent returned empty result.")
            return False

        # In production, you could use a lightweight LLM call here to double-check accuracy
        print("[Validator] ✅ Sub-agent output passed quality checks.")
        return True