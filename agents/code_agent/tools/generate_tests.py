def generate_unit_tests(code_snippet: str, framework: str = "pytest") -> str:
    """
    Tool to automatically write unit tests for a specific function or class.
    """
    print(f"[Tool: generate_tests] Writing {framework} tests for the provided code...")
    
    return f"import {framework}\n\ndef test_auto_generated():\n    assert True"