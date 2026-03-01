from apps.desktop.suvi.executor.sandbox import Sandbox

def test_sandbox_protection():
    # Should block Windows system folders
    assert Sandbox.is_safe_path("C:\\Windows\\System32") == False
    assert Sandbox.is_safe_path("C:\\Users\\Desktop\\MyProject") == True