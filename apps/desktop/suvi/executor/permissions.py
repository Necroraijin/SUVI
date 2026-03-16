from enum import Enum

class RiskLevel(Enum):
    SAFE = 1      # Clicks, scrolls, typing in non-system apps
    MODERATE = 2  # Opening system settings, clicking "Delete" (single file)
    DANGEROUS = 3 # Formatting drives, terminal commands like 'rm', bulk deletion

def get_action_risk(action_name: str, args: dict) -> RiskLevel:
    """
    Analyzes an action and its arguments to determine the risk level.
    """
    action_name = action_name.lower()
    
    # Dangerous commands
    dangerous_keywords = ["rm ", "format ", "del /s", "drop table", "shutdown", "reboot"]
    if action_name == "type_text_at" or action_name == "type":
        text = str(args.get("text", "")).lower()
        if any(k in text for k in dangerous_keywords):
            return RiskLevel.DANGEROUS
            
    # Moderate commands
    moderate_keywords = ["delete", "remove", "uninstall", "settings", "control panel"]
    if action_name == "click_at" or action_name == "click":
        pass
        
    return RiskLevel.SAFE
