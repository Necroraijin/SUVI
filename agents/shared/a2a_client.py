import json
from agents.shared.models import AgentMessage, AgentResponse

class A2AClient:
    """Handles communication between Vertex AI sub-agents."""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name

    async def send_task(self, target_agent: str, task: str, context: dict = None) -> AgentResponse:
        print(f"[{self.agent_name} -> {target_agent}] Dispatching task: {task}")
        
        message = AgentMessage(
            sender=self.agent_name,
            receiver=target_agent,
            task=task,
            context=context or {}
        )
        
        # TODO: Wire this to Google Cloud Pub/Sub or the FastAPI Gateway for real routing
        # For now, simulate a successful handoff
        
        return AgentResponse(
            status="success",
            result=f"Task '{task}' acknowledged by {target_agent}."
        )