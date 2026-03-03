"""SUVI Constants - Permission tiers and segment configurations."""

from shared.constants.permissions import (
    PermissionTier,
    PermissionChecker,
    PermissionResult,
    ACTION_TIER_MAP,
    TIER_DESCRIPTIONS,
    DEFAULT_USER_TIER_THRESHOLD,
)

from shared.constants.segments import (
    SegmentConfig,
    SEGMENTS,
    SEGMENT_ARC_SPAN,
    SEGMENT_GAP,
    SEGMENT_COLORS_RGB,
    get_segment_by_id,
    get_segment_at_angle,
)

__all__ = [
    # Permissions
    "PermissionTier",
    "PermissionChecker",
    "PermissionResult",
    "ACTION_TIER_MAP",
    "TIER_DESCRIPTIONS",
    "DEFAULT_USER_TIER_THRESHOLD",
    # Segments
    "SegmentConfig",
    "SEGMENTS",
    "SEGMENT_ARC_SPAN",
    "SEGMENT_GAP",
    "SEGMENT_COLORS_RGB",
    "get_segment_by_id",
    "get_segment_at_angle",
]
