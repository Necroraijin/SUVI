import json
from agents.shared import A2AClient, AgentResponse
from agents.shared.telemetry import TelemetryLogger

class TaskRouter:
    """Analyzes the user's input and routes it to the correct specialized sub-agent."""
    
    def __init__(self):
        # Initialize internal communication lines to the sub-agents
        self.code_agent = A2AClient("Agent_Code")
        self.browser_agent = A2AClient("Agent_Browser")
        self.file_agent = A2AClient("Agent_FileSystem")
        self.telemetry = TelemetryLogger()

    async def route_request(self, user_prompt: str, context: dict) -> AgentResponse:
        """Determines the intent and dispatches the task."""
        
        # In a full Vertex AI implementation, we would use Gemini to classify the intent.
        # For this local skeleton, we use basic keyword routing to simulate the A2A handoff.
        
        prompt_lower = user_prompt.lower()
        target_agent = None
        task = user_prompt
        
        # 1. Intent Classification
        if any(keyword in prompt_lower for keyword in ["code", "script", "debug", "python"]):
            target_agent = self.code_agent
            
        elif any(keyword in prompt_lower for keyword in ["search", "web", "browser", "look up"]):
            target_agent = self.browser_agent
            
        elif any(keyword in prompt_lower for keyword in ["file", "read", "write", "directory"]):
            target_agent = self.file_agent
            
        else:
            # If no specific agent is needed, the Orchestrator handles it directly
            return AgentResponse(
                status="success",
                result="I can answer that directly.",
                data={"direct_reply": True}
            )

        # 2. Dispatch Task
        print(f"[Router] Intent classified. Routing to {target_agent.agent_name}...")
        
        # Start telemetry timer
        import time
        start_time = time.time()
        
        response = await target_agent.send_task(target_agent.agent_name, task, context)
        
        # Log the latency
        latency = (time.time() - start_time) * 1000
        self.telemetry.log_action("Orchestrator", f"Routed to {target_agent.agent_name}", tokens=150, latency_ms=latency)
        
        return response