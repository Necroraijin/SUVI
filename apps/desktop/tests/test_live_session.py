from apps.desktop.suvi.services.memory_cache import MemoryCache

def test_memory_cache():
    cache = MemoryCache()
    cache.set("user_name", "Sunidhi")
    assert cache.get("user_name") == "Sunidhi"
    assert cache.get("non_existent") == None