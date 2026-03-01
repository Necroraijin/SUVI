def format_read_file(file_path: str) -> dict:
    """Tool to command the desktop to read a local file."""
    print(f"[Tool: read_file] Formatting command to read: {file_path}")
    return {
        "action": "read_file",
        "args": {"file_path": file_path}
    }