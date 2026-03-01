class MemoryCache:
    """A thread-safe local cache to minimize database reads."""
    def __init__(self):
        self._store = {}

    def set(self, key: str, value: any):
        self._store[key] = value
        
    def get(self, key: str, default=None):
        return self._store.get(key, default)
        
    def clear(self):
        self._store.clear()