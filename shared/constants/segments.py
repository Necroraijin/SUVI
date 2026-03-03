"""Segment Configuration - Action Ring visual segment definitions.

Defines the 8 segments of the Action Ring, their colors, labels, and angles.
These map to the different agent capabilities.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SegmentConfig:
    """Configuration for a single Action Ring segment."""
    id: str
    label: str
    color: str  # Hex color
    angle_start: float  # Degrees from top (clockwise)
    icon: Optional[str] = None
    description: Optional[str] = None


# The 8 Action Ring segments
SEGMENTS: list[SegmentConfig] = [
    SegmentConfig(
        id="code",
        label="Code",
        color="#10B981",  # Emerald green
        angle_start=337.5,
        description="Code generation, refactoring, debugging"
    ),
    SegmentConfig(
        id="browse",
        label="Browse",
        color="#7C3AED",  # Purple
        angle_start=22.5,
        description="Web browsing and automation"
    ),
    SegmentConfig(
        id="write",
        label="Write",
        color="#D97706",  # Amber
        angle_start=67.5,
        description="Content writing and editing"
    ),
    SegmentConfig(
        id="search",
        label="Search",
        color="#0D9488",  # Teal
        angle_start=112.5,
        description="Web search and information retrieval"
    ),
    SegmentConfig(
        id="file",
        label="File",
        color="#2563EB",  # Blue
        angle_start=157.5,
        description="File operations and management"
    ),
    SegmentConfig(
        id="app",
        label="App",
        color="#4F46E5",  # Indigo
        angle_start=202.5,
        description="Application launching and control"
    ),
    SegmentConfig(
        id="email",
        label="Email",
        color="#DC2626",  # Red
        angle_start=247.5,
        description="Email composition and management"
    ),
    SegmentConfig(
        id="data",
        label="Data",
        color="#475569",  # Slate
        angle_start=292.5,
        description="Data analysis and visualization"
    ),
]


# Arc span for each segment (45 degrees with 5 degree gap)
SEGMENT_ARC_SPAN = 40.0
SEGMENT_GAP = 5.0


# Segment colors as RGB tuples for gradient calculations
SEGMENT_COLORS_RGB: dict[str, tuple[int, int, int]] = {
    "code": (16, 185, 129),
    "browse": (124, 58, 237),
    "write": (217, 119, 6),
    "search": (13, 148, 136),
    "file": (37, 99, 235),
    "app": (79, 70, 229),
    "email": (220, 38, 38),
    "data": (71, 85, 105),
}


def get_segment_by_id(segment_id: str) -> Optional[SegmentConfig]:
    """Get segment configuration by ID."""
    for seg in SEGMENTS:
        if seg.id == segment_id:
            return seg
    return None


def get_segment_at_angle(angle: float) -> Optional[SegmentConfig]:
    """Get segment at a given angle (in degrees)."""
    normalized_angle = angle % 360

    for seg in SEGMENTS:
        end_angle = (seg.angle_start + SEGMENT_ARC_SPAN) % 360

        if end_angle > seg.angle_start:
            if seg.angle_start <= normalized_angle < end_angle:
                return seg
        else:  # Wraps around 360
            if normalized_angle >= seg.angle_start or normalized_angle < end_angle:
                return seg

    return None
