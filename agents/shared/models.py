from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class AgentMessage(BaseModel):
    """The standard envelope for sending a task to another agent."""
    sender: str
    receiver: str
    task: str
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)

class AgentResponse(BaseModel):
    """The standard reply when a sub-agent finishes its task."""
    status: str # e.g., "success", "failed", "requires_clarification"
    result: str
    data: Optional[Dict[str, Any]] = Field(default_factory=dict)