from enum import Enum, auto
from dataclasses import dataclass

class RingState(Enum):
    IDLE = auto()
    LISTENING = auto()
    THINKING = auto()
    EXECUTING = auto()
    DONE = auto()
    ERROR = auto()

@dataclass
class RingVisualState:
    ring_radius: float = 24.0      # Animates from 24 (idle) to 150 (expanded)
    ring_opacity: float = 0.7      # 0.7 idle, 1.0 active
    orb_glow: float = 0.0          # Driven by mic amplitude later
    arc_progress: float = 0.0      # Task completion percentage
    active_segment: int = -1       # Which agent is active
    rotation_angle: float = 0.0    # For the thinking state