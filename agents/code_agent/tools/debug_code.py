def debug_existing_code(code_snippet: str, error_message: str) -> str:
    """
    Tool to analyze a broken piece of code and an error trace to find the fix.
    """
    print(f"[Tool: debug_code] Analyzing error: {error_message}")
    
    return f"# Fix for error: {error_message}\n# Note: Check async event loop initialization and imports."