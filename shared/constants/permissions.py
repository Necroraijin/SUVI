"""Permission Tier System - Security model for desktop action execution.

Each tier defines what actions the system can perform without explicit user approval.
Higher tiers require confirmation before execution.
"""

from enum import IntEnum
from typing import Optional
from dataclasses import dataclass

from shared.suvi_types import ActionType, PermissionTier


# Mapping of action types to required permission tiers
ACTION_TIER_MAP: dict[ActionType, PermissionTier] = {
    # Tier 0 - Observe (no user approval needed)
    ActionType.SCREENSHOT: PermissionTier.TIER_0_OBSERVE,
    ActionType.BROWSER_READ: PermissionTier.TIER_0_OBSERVE,
    ActionType.CLIPBOARD_READ: PermissionTier.TIER_0_OBSERVE,

    # Tier 1 - Interact (no user approval needed)
    ActionType.MOUSE_CLICK: PermissionTier.TIER_1_INTERACT,
    ActionType.MOUSE_MOVE: PermissionTier.TIER_1_INTERACT,
    ActionType.TYPE_TEXT: PermissionTier.TIER_1_INTERACT,

    # Tier 2 - Operate (auto-approved but logged)
    ActionType.LAUNCH_APP: PermissionTier.TIER_2_OPERATE,
    ActionType.CLOSE_APP: PermissionTier.TIER_2_OPERATE,
    ActionType.CLIPBOARD_WRITE: PermissionTier.TIER_2_OPERATE,

    # Tier 3 - Modify (requires confirmation)
    ActionType.READ_FILE: PermissionTier.TIER_3_MODIFY,
    ActionType.WRITE_FILE: PermissionTier.TIER_3_MODIFY,
    ActionType.DELETE_FILE: PermissionTier.TIER_3_MODIFY,
    ActionType.LIST_DIRECTORY: PermissionTier.TIER_3_MODIFY,
    ActionType.BROWSER_NAVIGATE: PermissionTier.TIER_3_MODIFY,
    ActionType.BROWSER_CLICK: PermissionTier.TIER_3_MODIFY,
    ActionType.BROWSER_TYPE: PermissionTier.TIER_3_MODIFY,
    ActionType.EXECUTE_SCRIPT: PermissionTier.TIER_3_MODIFY,

    # Tier 4 - System (requires PIN/biometric)
    ActionType.PRESS_HOTKEY: PermissionTier.TIER_4_SYSTEM,
}


# Human-readable descriptions for each tier
TIER_DESCRIPTIONS: dict[PermissionTier, str] = {
    PermissionTier.TIER_0_OBSERVE: "Observe - Read-only actions like screenshots and clipboard",
    PermissionTier.TIER_1_INTERACT: "Interact - Basic mouse and keyboard actions",
    PermissionTier.TIER_2_OPERATE: "Operate - App management and clipboard operations",
    PermissionTier.TIER_3_MODIFY: "Modify - File operations and browser automation",
    PermissionTier.TIER_4_SYSTEM: "System - Critical system-level actions",
}


# Default user-configured tier thresholds
DEFAULT_USER_TIER_THRESHOLD = PermissionTier.TIER_2_OPERATE


@dataclass
class PermissionResult:
    """Result of a permission check."""
    granted: bool
    tier: PermissionTier
    requires_confirmation: bool
    message: str


class PermissionChecker:
    """Validates if an action can be executed based on permission tiers."""

    def __init__(self, user_tier_threshold: PermissionTier = DEFAULT_USER_TIER_THRESHOLD):
        """
        Initialize permission checker.

        Args:
            user_tier_threshold: Maximum tier the user has auto-approved
        """
        self.user_tier_threshold = user_tier_threshold

    def check_action(self, action_type: ActionType) -> PermissionResult:
        """
        Check if an action is permitted.

        Args:
            action_type: Type of action to check

        Returns:
            PermissionResult with the decision
        """
        required_tier = ACTION_TIER_MAP.get(action_type, PermissionTier.TIER_4_SYSTEM)

        if required_tier <= self.user_tier_threshold:
            return PermissionResult(
                granted=True,
                tier=required_tier,
                requires_confirmation=False,
                message=f"Action {action_type.value} auto-approved (Tier {required_tier.value})"
            )
        else:
            return PermissionResult(
                granted=False,
                tier=required_tier,
                requires_confirmation=True,
                message=f"Action {action_type.value} requires confirmation (Tier {required_tier.value})"
            )

    def set_user_threshold(self, tier: PermissionTier):
        """Update the user's tier threshold."""
        self.user_tier_threshold = tier

    def get_tier_for_action(self, action_type: ActionType) -> PermissionTier:
        """Get the required tier for an action type."""
        return ACTION_TIER_MAP.get(action_type, PermissionTier.TIER_4_SYSTEM)
