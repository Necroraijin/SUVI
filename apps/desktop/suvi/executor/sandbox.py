import os

class Sandbox:
    """Prevents SUVI from accessing critical OS directories on your Windows machine."""
    
    RESTRICTED_DIRS = [
        "C:\\Windows", 
        "C:\\Program Files", 
        "C:\\Program Files (x86)"
    ]

    @classmethod
    def is_safe_path(cls, target_path: str) -> bool:
        abs_path = os.path.abspath(target_path)
        for restricted in cls.RESTRICTED_DIRS:
            if abs_path.lower().startswith(restricted.lower()):
                return False
        return True