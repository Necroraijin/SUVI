def format_write_file(file_path: str, content: str) -> dict:
    """Tool to command the desktop to write code to a local file."""
    print(f"[Tool: write_file] Formatting command to write to: {file_path}")
    return {
        "action": "write_file",
        "args": {"file_path": file_path, "content": content}
    }