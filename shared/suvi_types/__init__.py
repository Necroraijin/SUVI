"""SUVI Shared Data Types - Pydantic models for the entire system."""

from enum import Enum
from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ActionType(str, Enum):
    """Types of actions that can be executed on the desktop."""
    MOUSE_CLICK = "mouse_click"
    MOUSE_MOVE = "mouse_move"
    MOUSE_DRAG = "mouse_drag"
    TYPE_TEXT = "type_text"
    PRESS_HOTKEY = "press_hotkey"
    LAUNCH_APP = "launch_app"
    CLOSE_APP = "close_app"
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    DELETE_FILE = "delete_file"
    LIST_DIRECTORY = "list_directory"
    BROWSER_NAVIGATE = "browser_navigate"
    BROWSER_CLICK = "browser_click"
    BROWSER_TYPE = "browser_type"
    BROWSER_READ = "browser_read"
    SCREENSHOT = "screenshot"
    EXECUTE_SCRIPT = "execute_script"
    CLIPBOARD_READ = "clipboard_read"
    CLIPBOARD_WRITE = "clipboard_write"


class PermissionTier(int, Enum):
    """Permission tier levels for action execution."""
    TIER_0_OBSERVE = 0  # Screenshot, read screen, clipboard read
    TIER_1_INTERACT = 1  # Click, type, scroll
    TIER_2_OPERATE = 2  # Paste, open apps, clipboard write
    TIER_3_MODIFY = 3  # Create/delete files, run scripts, close apps
    TIER_4_SYSTEM = 4  # System settings, installs, network config


class ActionStatus(str, Enum):
    """Status of an action execution."""
    PENDING = "pending"
    APPROVED = "approved"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class Action(BaseModel):
    """Represents a desktop action to be executed."""
    id: str = Field(default_factory=lambda: f"action_{datetime.now().timestamp()}")
    action_type: ActionType
    tier: PermissionTier
    args: dict[str, Any] = Field(default_factory=dict)
    status: ActionStatus = ActionStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    executed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[str] = None
    error: Optional[str] = None
    requires_confirmation: bool = False
    can_undo: bool = False

    class Config:
        use_enum_values = True


class TaskStatus(str, Enum):
    """Status of a user task."""
    RECEIVED = "received"
    ROUTING = "routing"
    PROCESSING = "processing"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task(BaseModel):
    """Represents a user task from voice/text input."""
    id: str = Field(default_factory=lambda: f"task_{datetime.now().timestamp()}")
    user_input: str
    intent: Optional[str] = None
    status: TaskStatus = TaskStatus.RECEIVED
    actions: list[Action] = Field(default_factory=list)
    agent_results: list[dict[str, Any]] = Field(default_factory=list)
    memory_context: Optional[dict[str, Any]] = None
    screen_frame: Optional[bytes] = None
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    total_tokens: int = 0
    error: Optional[str] = None

    class Config:
        use_enum_values = True


class AgentType(str, Enum):
    """Types of agents in the system."""
    ORCHESTRATOR = "orchestrator"
    CODE = "code"
    TEXT = "text"
    BROWSER = "browser"
    SEARCH = "search"
    MEMORY = "memory"
    EMAIL = "email"
    DATA = "data"


class AgentResultStatus(str, Enum):
    """Status of an agent execution result."""
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"
    TIMEOUT = "timeout"


class AgentResult(BaseModel):
    """Result from an agent execution."""
    id: str = Field(default_factory=lambda: f"result_{datetime.now().timestamp()}")
    agent_type: AgentType
    task_id: str
    status: AgentResultStatus
    output: Optional[Any] = None
    error: Optional[str] = None
    tokens_used: int = 0
    execution_time_ms: int = 0
    artifacts: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        use_enum_values = True


class SessionState(BaseModel):
    """Current state of a user session."""
    session_id: str
    user_id: str
    is_active: bool = True
    ring_state: str = "idle"
    current_agent: Optional[AgentType] = None
    current_task: Optional[Task] = None
    conversation_history: list[dict[str, str]] = Field(default_factory=list)
    memory_tier_hot: list[dict[str, Any]] = Field(default_factory=list)
    memory_tier_warm: list[dict[str, Any]] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=datetime.now)
    last_activity_at: datetime = Field(default_factory=datetime.now)


class AgentCapability(BaseModel):
    """Agent capability as per A2A protocol."""
    name: str
    description: str
    input_modes: list[str] = Field(default_factory=lambda: ["text", "audio"])
    output_modes: list[str] = Field(default_factory=lambda: ["text", "audio"])
    parameters: Optional[dict[str, Any]] = None


class AgentCard(BaseModel):
    """A2A Agent Card - capability declaration."""
    agent_id: str
    name: str
    description: str
    url: str
    provider: dict[str, str]
    version: str = "1.0.0"
    capabilities: list[AgentCapability]
    skills: list[str] = Field(default_factory=list)
    authentication: dict[str, str] = Field(default_factory=lambda: {"type": "none"})
    supports_streaming: bool = False
