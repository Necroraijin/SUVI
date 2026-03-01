import json
from pathlib import Path

class PermissionManager:
    """Stores and checks user-approved permissions for high-risk actions."""
    def __init__(self, config_file="suvi_permissions.json"):
        self.config_path = Path(config_file)
        self.allowed_actions = self._load()

    def _load(self):
        if self.config_path.exists():
            return json.loads(self.config_path.read_text())
        # Default strict permissions
        return {
            "auto_click": True, 
            "file_read": True,
            "file_write": False, 
            "shell_execute": False
        }

    def has_permission(self, action: str) -> bool:
        return self.allowed_actions.get(action, False)