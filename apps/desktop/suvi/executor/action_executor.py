import asyncio
import pyautogui
from PyQt6.QtCore import QObject, pyqtSignal

from apps.desktop.suvi.executor.desktop import DesktopExecutor
from apps.desktop.suvi.executor.kill_switch import KillSwitch
from apps.desktop.suvi.executor.filesystem import FileSystemExecutor
from apps.desktop.suvi.executor.browser import BrowserExecutor

class ActionExecutor(QObject):
    """Routes Vertex AI tool calls to the correct OS modules."""

    action_started = pyqtSignal(str)
    action_completed = pyqtSignal(str, str) 
    action_failed = pyqtSignal(str)
    # Signal to request UI confirmation from the AppController
    permission_required = pyqtSignal(str, str) # (tool_name, description)
    # Signal emitted when user makes a decision in the UI
    action_resumed = pyqtSignal(bool) # (approved)

    def __init__(self):
        super().__init__()
        self.desktop = DesktopExecutor()
        self.filesystem = FileSystemExecutor()
        self.browser = BrowserExecutor()
        self._pending_call = None
        self._resume_event = asyncio.Event()

    async def execute_tool_call(self, tool_call: dict):
        tool_name = tool_call.get("name")
        args = tool_call.get("args", {})

        if KillSwitch.is_active():
            self.action_failed.emit("Kill switch is active. Ignoring commands.")
            return

        # 1. Check Permission Tier
        from apps.desktop.suvi.executor.permissions import PermissionManager
        tier = PermissionManager.get_tier(tool_name)

        if PermissionManager.requires_confirmation(tier):
            print(f"[Executor] {tool_name} requires confirmation (Tier {tier}). Pausing...")
            self.permission_required.emit(tool_name, f"{tool_name} with args: {args}")

            # Wait for user input from the UI
            self._resume_event.clear()
            await self._resume_event.wait()

            if not self._approved:
                self.action_failed.emit(f"Action '{tool_name}' rejected by user.")
                return

        self.action_started.emit(f"Executing: {tool_name}")
        print(f"[Executor] Routing tool call: {tool_name}")

        try:
            result = ""

            # --- Desktop Routing ---
            if tool_name == "mouse_click":
                result = await self.desktop.click(args.get("x"), args.get("y"))
            elif tool_name == "type_text":
                result = await self.desktop.type_text(args.get("text"))
            elif tool_name == "press_hotkey":
                result = await self.desktop.press_hotkey(args.get("keys"))

            # --- File System Routing ---
            elif tool_name == "read_file":
                result = self.filesystem.read_file(args.get("file_path"))
            elif tool_name == "write_file":
                result = self.filesystem.write_file(args.get("file_path"), args.get("content"))
            elif tool_name == "list_directory":
                result = self.filesystem.list_directory(args.get("dir_path"))

            # --- Browser Routing ---
            elif tool_name == "browser_navigate":
                result = await self.browser.navigate(args.get("url"))
            elif tool_name == "browser_read":
                result = await self.browser.get_page_content()

            else:
                result = f"Error: Unknown tool name '{tool_name}'."
                print(f"[Executor] {result}")

            self.action_completed.emit("Action Success", result)

        except pyautogui.FailSafeException:
            msg = "Action aborted by user moving mouse to screen corner."
            print(f"[CRITICAL] {msg}")
            KillSwitch.activate()
            self.action_failed.emit(msg)
        except Exception as e:
            print(f"[Executor] Task failed: {e}")
            self.action_failed.emit(str(e))

    def handle_user_decision(self, approved: bool):
        """Called by AppController when user interacts with ConfirmDialog."""
        self._approved = approved
        self._resume_event.set()