from agents.orchestrator.system_prompt import ORCHESTRATOR_PROMPT
from agents.orchestrator.router import TaskRouter
from agents.shared import MemoryClient
from shared.suvi_types import AgentResultStatus

class SuviOrchestrator:
    """The master control agent for SUVI."""
    
    def __init__(self):
        self.system_prompt = ORCHESTRATOR_PROMPT
        self.router = TaskRouter()
        self.memory = MemoryClient()

    async def process_user_input(self, text_input: str) -> str:
        """The main entry point for all user commands."""
        print(f"\n[SUVI Orchestrator] Received input: '{text_input}'")
        
        # 1. Fetch relevant long-term memory
        context_str = self.memory.retrieve_context(text_input)
        
        # 2. Route the task to the correct sub-agent
        # Context needs to be a dict for A2A
        context = {"memory": context_str}
        result = await self.router.route_request(text_input, context)
        
        # 3. Process the sub-agent's response
        if result.status == AgentResultStatus.SUCCESS:
            if result.artifacts.get("direct_reply"):
                return result.output or "I can answer that directly."
            else:
                return f"Task completed: {result.output}"
        else:
            return f"Sub-agent encountered an issue: {result.error}"