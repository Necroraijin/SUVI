class KillSwitch:
    """Global emergency state to instantly halt all agent actions."""
    
    _triggered = False

    @classmethod
    def activate(cls):
        print("[CRITICAL] Kill Switch Activated. Blocking OS execution.")
        cls._triggered = True

    @classmethod
    def reset(cls):
        print("[System] Kill Switch Reset. OS execution restored.")
        cls._triggered = False

    @classmethod
    def is_active(cls):
        return cls._triggered