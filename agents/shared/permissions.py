from enum import Enum

class AgentScope(Enum):
    """Defines what an agent is allowed to do."""
    READ_ONLY = "read_only"       # Can search, read files, and answer questions
    WRITE_SAFE = "write_safe"     # Can write code or notes, but not execute
    EXECUTE = "execute"           # Can run Python scripts or terminal commands
    ADMIN = "admin"               # Full system access (Orchestrator only)

class CloudPermissions:
    """Validates if a specific sub-agent has the clearance for a requested tool."""
    
    def __init__(self, agent_name: str, scope: AgentScope):
        self.agent_name = agent_name
        self.scope = scope

    def can_modify_system(self) -> bool:
        """Checks if the agent is allowed to change files or run code."""
        allowed = self.scope in [AgentScope.EXECUTE, AgentScope.ADMIN]
        if not allowed:
            print(f"[Security] 🛑 Blocked: '{self.agent_name}' attempted an unauthorized system modification.")
        return allowed