import pyautogui
import asyncio
from PyQt6.QtWidgets import QMessageBox
from .permissions import RiskLevel, get_action_risk

class ActionDispatcher:
    """
    The secure gatekeeper for all physical computer actions.
    Wraps PyAutoGUI with safety checks and user confirmation dialogs.
    Includes environment-aware verification to prevent launching non-existent apps.
    """
    def __init__(self, ui_widget=None, env_scanner=None):
        self.ui = ui_widget
        self.env_scanner = env_scanner
        self.screen_width, self.screen_height = pyautogui.size()
        # Default safety: failsafe moves mouse to corner to abort
        pyautogui.FAILSAFE = True

    def is_autopilot_enabled(self) -> bool:
        """Returns True if the user has enabled Autopilot Mode."""
        if self.ui and hasattr(self.ui, 'autopilot_btn'):
            return self.ui.autopilot_btn.isChecked()
        return False

    async def execute(self, action_name: str, args: dict) -> str:
        """
        Main entry point for executing an action.
        Returns "success", "user_denied", or "error: message".
        """
        risk = get_action_risk(action_name, args)
        
        # Check Autopilot State from UI
        autopilot_on = self.is_autopilot_enabled()

        # Dangerous actions ALWAYS require confirmation (Voice or Dialog)
        if risk == RiskLevel.DANGEROUS:
            confirmed = await self._request_confirmation(
                "Critical Safety Alert",
                f"SUVI is attempting a dangerous action: {action_name}. Do you want to allow this?"
            )
            if not confirmed:
                return "user_denied"
        
        # Moderate actions only require confirmation if Autopilot is OFF
        elif risk == RiskLevel.MODERATE and not autopilot_on:
            confirmed = await self._request_confirmation(
                "Action Confirmation",
                f"SUVI wants to: {action_name}. Allow?"
            )
            if not confirmed:
                return "user_denied"
        
        try:
            print(f"🎬 [Dispatcher] Executing: {action_name}")
            
            # ═══════════════════════════════════════════════════════════
            # Computer Use BUILT-IN actions (normalized 0-999 coordinates)
            # ═══════════════════════════════════════════════════════════
            
            if action_name == "click_at":
                x, y = self._scale_coords(args.get("x", 0), args.get("y", 0))
                pyautogui.click(x, y)

            elif action_name == "type_text_at":
                x, y = self._scale_coords(args.get("x", 0), args.get("y", 0))
                text = args.get("text", "")
                press_enter = args.get("press_enter", False)
                clear_before = args.get("clear_before_typing", False)
                pyautogui.click(x, y)
                await asyncio.sleep(0.1)
                if clear_before:
                    pyautogui.hotkey('ctrl', 'a')
                    pyautogui.press('backspace')
                pyautogui.write(text, interval=0.02)
                if press_enter:
                    pyautogui.press('enter')

            elif action_name == "key_combination":
                keys_str = args.get("keys", "")
                # Convert "Control+A" format to pyautogui hotkey args
                keys = [k.strip().lower() for k in keys_str.split("+")]
                # Map common key names
                key_map = {"control": "ctrl", "command": "ctrl", "meta": "ctrl"}
                keys = [key_map.get(k, k) for k in keys]
                pyautogui.hotkey(*keys)

            elif action_name == "hover_at":
                x, y = self._scale_coords(args.get("x", 0), args.get("y", 0))
                pyautogui.moveTo(x, y)

            elif action_name == "scroll_document":
                direction = args.get("direction", "down")
                clicks = 5 if direction == "up" else -5
                pyautogui.scroll(clicks)

            elif action_name == "scroll_at":
                x, y = self._scale_coords(args.get("x", 0), args.get("y", 0))
                direction = args.get("direction", "down")
                magnitude = args.get("magnitude", 3)
                pyautogui.moveTo(x, y)
                clicks = magnitude if direction == "up" else -magnitude
                pyautogui.scroll(int(clicks))

            elif action_name == "drag_and_drop":
                sx, sy = self._scale_coords(args.get("x", 0), args.get("y", 0))
                ex, ey = self._scale_coords(args.get("destination_x", 0), args.get("destination_y", 0))
                pyautogui.moveTo(sx, sy)
                pyautogui.dragTo(ex, ey, duration=0.5)

            elif action_name == "open_web_browser":
                import webbrowser
                await asyncio.to_thread(webbrowser.open, "about:blank")

            elif action_name == "navigate":
                import webbrowser
                url = args.get("url", "")
                if url and not url.startswith("http"):
                    url = "https://" + url
                await asyncio.to_thread(webbrowser.open, url)

            elif action_name == "wait_5_seconds":
                await asyncio.sleep(5)

            elif action_name == "go_back":
                pyautogui.hotkey('alt', 'left')

            elif action_name == "go_forward":
                pyautogui.hotkey('alt', 'right')

            elif action_name == "search":
                # Browser search — typically Ctrl+L to focus address bar, then type
                query = args.get("query", "")
                pyautogui.hotkey('ctrl', 'l')
                await asyncio.sleep(0.2)
                pyautogui.write(query, interval=0.02)
                pyautogui.press('enter')

            # ═══════════════════════════════════════════════════════════
            # Custom SUVI functions
            # ═══════════════════════════════════════════════════════════
            
            elif action_name == "launch_application":
                app_name = args.get("app_name", "").lower()
                import subprocess
                import sys
                
                # ── Runtime Environment Verification ──
                # Check if the app is actually installed before trying to launch
                if self.env_scanner and not self._is_app_launchable(app_name):
                    # App not installed — provide helpful fallback info
                    alternatives = self._get_alternatives_for(app_name)
                    alt_msg = f" Available alternatives: {', '.join(alternatives)}" if alternatives else ""
                    print(f"🚫 [Dispatcher] App '{app_name}' is NOT installed.{alt_msg}")
                    return f"APP_NOT_FOUND: '{app_name}' is not installed on this computer.{alt_msg}"
                
                app_map = {
                    "chrome": "chrome" if sys.platform == "win32" else "google-chrome",
                    "google chrome": "chrome",
                    "firefox": "firefox",
                    "notepad": "notepad",
                    "calculator": "calc",
                    "edge": "msedge",
                    "microsoft edge": "msedge",
                    "terminal": "cmd",
                    "windows terminal": "wt",
                    "explorer": "explorer",
                    "file explorer": "explorer",
                    "spotify": "spotify",
                    "discord": "discord",
                    "vlc": "vlc",
                    "vlc media player": "vlc",
                }
                cmd = app_map.get(app_name, app_name)

                if sys.platform == "win32":
                    await asyncio.to_thread(subprocess.Popen, f"start {cmd}", shell=True)
                elif sys.platform == "darwin":
                    await asyncio.to_thread(subprocess.Popen, ["open", "-a", cmd])
                else:
                    await asyncio.to_thread(subprocess.Popen, [cmd])
                    
            elif action_name == "open_url":
                import webbrowser
                url = args.get("url", "")
                if not url.startswith("http"):
                    url = "https://" + url
                await asyncio.to_thread(webbrowser.open, url)

            # Legacy action names (kept for backward compat)
            elif action_name == "right_click_at":
                x, y = self._scale_coords(args.get("x", 0), args.get("y", 0))
                pyautogui.rightClick(x, y)

            elif action_name == "double_click_at":
                x, y = self._scale_coords(args.get("x", 0), args.get("y", 0))
                pyautogui.doubleClick(x, y)

            elif action_name == "type_text":
                pyautogui.write(args.get("text", ""), interval=0.02)
                
            elif action_name == "press_key":
                pyautogui.press(args.get("key", "enter"))
                
            elif action_name == "wait":
                seconds = args.get("seconds", 1)
                await asyncio.sleep(seconds)
            
            else:
                print(f"⚠️ Unknown action: {action_name}. Skipping.")
                return f"unknown_action: {action_name}"
                
            return "success"
            
        except pyautogui.FailSafeException:
            print("🛑 FAILSAFE TRIGGERED")
            return "error: Failsafe triggered. Mouse moved to corner."
        except Exception as e:
            print(f"❌ Execution Error: {e}")
            return f"error: {type(e).__name__}: {str(e)}"

    def _scale_coords(self, x: int, y: int) -> tuple[int, int]:
        """Convert 0-1000 normalized coordinates to real screen pixels."""
        real_x = int(x / 1000 * self.screen_width)
        real_y = int(y / 1000 * self.screen_height)
        return real_x, real_y

    async def _request_confirmation(self, title: str, message: str) -> bool:
        """Shows a non-blocking confirmation dialog."""
        print(f"⚠️ SAFETY CHECK: {message}")
        if not self.ui:
            return True # Fallback
            
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        msg_box.setWindowFlags(msg_box.windowFlags() | msg_box.windowFlags().WindowStaysOnTopHint)
        
        ret = msg_box.exec()
        return ret == QMessageBox.StandardButton.Yes

    def _is_app_launchable(self, app_name: str) -> bool:
        """
        Check if an app is installed and launchable.
        Uses the EnvironmentScanner for intelligent lookup.
        """
        if not self.env_scanner:
            return True  # No scanner = assume everything is available
        
        # Built-in system apps that are always available
        always_available = {
            "notepad", "calculator", "calc", "cmd", "powershell",
            "explorer", "file explorer", "paint", "snipping tool",
            "task manager", "control panel", "settings",
        }
        if app_name.lower() in always_available:
            return True
        
        # Check via scanner
        if self.env_scanner.is_app_installed(app_name):
            return True
        
        # Common alias check (e.g., "chrome" should match "Google Chrome")
        common_aliases = {
            "chrome": "google chrome",
            "edge": "microsoft edge",
            "firefox": "mozilla firefox",
            "vscode": "visual studio code",
            "code": "visual studio code",
            "wt": "windows terminal",
        }
        resolved = common_aliases.get(app_name.lower(), app_name.lower())
        if resolved != app_name.lower() and self.env_scanner.is_app_installed(resolved):
            return True
        
        return False
    
    def _get_alternatives_for(self, app_name: str) -> list:
        """
        Given an app that's NOT installed, suggest alternatives
        based on the capability map.
        
        Example: "youtube" not installed → suggests browsers (for web-based access)
        """
        if not self.env_scanner:
            return []
        
        # Determine what capability the requested app would fill
        from apps.desktop.suvi.services.environment_scanner import APP_CAPABILITY_MAP
        
        app_lower = app_name.lower()
        target_caps = APP_CAPABILITY_MAP.get(app_lower, [])
        
        # If we can't map the app, guess based on keywords
        if not target_caps:
            keyword_cap_map = {
                "music": "music_player",
                "video": "video_player",
                "youtube": "browser",  # YouTube = use browser
                "browser": "browser",
                "edit": "text_editor",
                "code": "code_editor",
                "chat": "communication",
                "call": "video_call",
            }
            for keyword, cap in keyword_cap_map.items():
                if keyword in app_lower:
                    target_caps = [cap]
                    break
        
        # Find installed apps that share those capabilities
        alternatives = set()
        capabilities = self.env_scanner.get_capabilities()
        for cap in target_caps:
            if cap in capabilities:
                for alt_app in capabilities[cap]:
                    alternatives.add(alt_app)
        
        # Always suggest the default browser as a web fallback
        env = self.env_scanner.scan()
        default_browser = env.get("default_browser")
        if default_browser:
            alternatives.add(default_browser)
        
        return sorted(alternatives)
