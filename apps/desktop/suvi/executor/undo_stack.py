class UndoStack:
    """Tracks reversible actions (like moving a file) so SUVI can undo mistakes."""
    def __init__(self):
        self._stack = []

    def push(self, revert_action: dict):
        self._stack.append(revert_action)

    def pop(self):
        if not self._stack:
            return None
        return self._stack.pop()