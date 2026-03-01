from pathlib import Path

class FileSystemExecutor:
    """Handles reading, writing, and navigating the local file system safely."""

    def __init__(self, workspace_root=None):
        # Default to the current directory if no specific workspace is provided
        self.workspace = Path(workspace_root) if workspace_root else Path.cwd()

    def read_file(self, file_path: str) -> str:
        target = self.workspace / file_path
        if not target.exists() or not target.is_file():
            return f"Error: File not found at {target}"
        try:
            return target.read_text(encoding='utf-8')
        except Exception as e:
            return f"Error reading file: {e}"

    def write_file(self, file_path: str, content: str) -> str:
        target = self.workspace / file_path
        # Ensure the directory exists before writing
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            target.write_text(content, encoding='utf-8')
            return f"Successfully wrote {len(content)} characters to {target.name}"
        except Exception as e:
            return f"Error writing file: {e}"
            
    def list_directory(self, dir_path: str = ".") -> str:
        target = self.workspace / dir_path
        if not target.exists() or not target.is_dir():
            return f"Error: Directory not found at {target}"
        try:
            items = [f.name for f in target.iterdir()]
            return "\n".join(items) if items else "Directory is empty."
        except Exception as e:
            return f"Error listing directory: {e}"