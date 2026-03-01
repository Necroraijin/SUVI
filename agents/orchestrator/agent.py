from agents.orchestrator.system_prompt import ORCHESTRATOR_PROMPT
from agents.orchestrator.router import TaskRouter
from agents.shared import MemoryClient

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
        context = self.memory.retrieve_context(text_input)
        
        # 2. Route the task to the correct sub-agent
        response = await self.router.route_request(text_input, {"memory": context})
        
        # 3. Process the sub-agent's response
        if response.status == "success":
            if response.data.get("direct_reply"):
                return "This is a direct response from SUVI's Orchestrator."
            else:
                return f"Task completed by sub-agent: {response.result}"
        else:
            return f"Sub-agent encountered an issue: {response.result}"