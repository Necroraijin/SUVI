from shared.suvi_types import PermissionTier, ActionType

class PermissionManager:
    """Standardized permission tier mapping and enforcement."""
    
    # Map Tool Names to Tiers
    TOOL_TIERS = {
        # Tier 0 - Observe
        "screenshot": PermissionTier.TIER_0_OBSERVE,
        "browser_read": PermissionTier.TIER_0_OBSERVE,
        "clipboard_read": PermissionTier.TIER_0_OBSERVE,
        
        # Tier 1 - Interact
        "mouse_click": PermissionTier.TIER_1_INTERACT,
        "type_text": PermissionTier.TIER_1_INTERACT,
        "press_hotkey": PermissionTier.TIER_1_INTERACT,
        "scroll": PermissionTier.TIER_1_INTERACT,
        
        # Tier 2 - Operate
        "launch_app": PermissionTier.TIER_2_OPERATE,
        "clipboard_write": PermissionTier.TIER_2_OPERATE,
        
        # Tier 3 - Modify (Requires Confirmation)
        "write_file": PermissionTier.TIER_3_MODIFY,
        "delete_file": PermissionTier.TIER_3_MODIFY,
        "execute_script": PermissionTier.TIER_3_MODIFY,
        "close_app": PermissionTier.TIER_3_MODIFY,
        
        # Tier 4 - System (Highest Risk)
        "network_config": PermissionTier.TIER_4_SYSTEM,
    }

    @staticmethod
    def get_tier(tool_name: str) -> PermissionTier:
        return PermissionManager.TOOL_TIERS.get(tool_name, PermissionTier.TIER_3_MODIFY)

    @staticmethod
    def requires_confirmation(tier: PermissionTier) -> bool:
        return tier >= PermissionTier.TIER_3_MODIFY
