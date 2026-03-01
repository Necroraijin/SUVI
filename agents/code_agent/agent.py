from agents.shared.models import AgentMessage, AgentResponse
from agents.code_agent.system_prompt import CODE_AGENT_PROMPT

class CodeAgent:
    """The specialized sub-agent for programming and file system operations."""
    
    def __init__(self):
        self.system_prompt = CODE_AGENT_PROMPT
        self.agent_name = "Agent_Code"

    async def handle_task(self, message: AgentMessage) -> AgentResponse:
        """Processes a coding or file-system task."""
        print(f"[{self.agent_name}] Waking up to handle task: '{message.task}'")
        
        task_lower = message.task.lower()
        result_data = ""
        
        # 1. Simulate Tool Execution (Routing to the Desktop Executor)
        if "read" in task_lower or "analyze" in task_lower:
            print(f"[{self.agent_name}] Triggering desktop tool: read_file")
            result_data = f"Successfully read file contents from the local machine."
            
        elif "write" in task_lower or "create" in task_lower or "script" in task_lower:
            print(f"[{self.agent_name}] Triggering desktop tool: write_file")
            result_data = f"Successfully wrote new code to the local file system."
            
        elif "list" in task_lower or "directory" in task_lower:
            print(f"[{self.agent_name}] Triggering desktop tool: list_directory")
            result_data = f"Retrieved directory contents."
            
        else:
            result_data = "Executed general coding analysis."

        print(f"[{self.agent_name}] Task complete. Returning control to Orchestrator.")
        return AgentResponse(
            status="success",
            result=f"Code Agent action completed: {result_data}"
        )