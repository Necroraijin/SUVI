import pyautogui
import asyncio
from PyQt6.QtWidgets import QMessageBox
from .permissions import RiskLevel, get_action_risk

class ActionDispatcher:
    """
    Secure execution layer for all desktop actions.
    Converts Gemini Computer-Use actions into PyAutoGUI commands.
    """

    def __init__(self, ui_widget=None, env_scanner=None):
        self.ui = ui_widget
        self.env_scanner = env_scanner
        self.screen_width, self.screen_height = pyautogui.size()

        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.05

    def is_autopilot_enabled(self) -> bool:
        if self.ui and hasattr(self.ui, "autopilot_btn"):
            return self.ui.autopilot_btn.isChecked()
        return False

    async def execute(self, action_name: str, args: dict) -> str:
        risk = get_action_risk(action_name, args)
        autopilot = self.is_autopilot_enabled()

        if risk == RiskLevel.DANGEROUS:
            confirmed = await self._request_confirmation(
                "Critical Safety Alert",
                f"SUVI is attempting a dangerous action: {action_name}. Allow?",
            )
            if not confirmed:
                return "user_denied"

        elif risk == RiskLevel.MODERATE and not autopilot:
            confirmed = await self._request_confirmation(
                "Action Confirmation",
                f"SUVI wants to perform: {action_name}. Allow?",
            )
            if not confirmed:
                return "user_denied"

        try:
            print(f"🎬 [Dispatcher] Executing: {action_name} {args}")

            if action_name == "click_at":
                x, y = self._scale_coords(args.get("x"), args.get("y"))
                pyautogui.click(x, y)

            elif action_name == "double_click_at":
                x, y = self._scale_coords(args.get("x"), args.get("y"))
                pyautogui.doubleClick(x, y)

            elif action_name == "right_click_at":
                x, y = self._scale_coords(args.get("x"), args.get("y"))
                pyautogui.rightClick(x, y)

            elif action_name == "hover_at":
                x, y = self._scale_coords(args.get("x"), args.get("y"))
                pyautogui.moveTo(x, y)

            elif action_name == "drag_and_drop":
                sx, sy = self._scale_coords(args.get("x"), args.get("y"))
                ex, ey = self._scale_coords(
                    args.get("destination_x"), args.get("destination_y")
                )
                pyautogui.moveTo(sx, sy)
                pyautogui.dragTo(ex, ey, duration=0.4)

            elif action_name == "type_text":
                pyautogui.write(args.get("text", ""), interval=0.02)

            elif action_name == "type_text_at":
                x, y = self._scale_coords(args.get("x"), args.get("y"))
                pyautogui.click(x, y)

                await asyncio.sleep(0.15)

                if args.get("clear_before_typing"):
                    pyautogui.hotkey("ctrl", "a")
                    pyautogui.press("backspace")

                pyautogui.write(args.get("text", ""), interval=0.02)

                if args.get("press_enter"):
                    pyautogui.press("enter")

            elif action_name == "press_key":
                pyautogui.press(args.get("key", "enter"))

            elif action_name == "key_combination":
                keys = args.get("keys", "")
                if isinstance(keys, str):
                    keys = [k.strip().lower() for k in keys.split("+")]
                pyautogui.hotkey(*keys)

            elif action_name == "scroll_document":
                direction = args.get("direction", "down")
                pyautogui.scroll(400 if direction == "up" else -400)

            elif action_name == "scroll_at":
                x, y = self._scale_coords(args.get("x"), args.get("y"))
                pyautogui.moveTo(x, y)
                direction = args.get("direction", "down")
                magnitude = args.get("magnitude", 5)
                pyautogui.scroll(
                    magnitude * 100 if direction == "up" else -magnitude * 100
                )

            elif action_name == "wait":
                await asyncio.sleep(args.get("seconds", 1))

            elif action_name == "wait_5_seconds":
                await asyncio.sleep(5)

            elif action_name == "go_back":
                pyautogui.hotkey("alt", "left")

            elif action_name == "go_forward":
                pyautogui.hotkey("alt", "right")

            elif action_name == "search":
                query = args.get("query", "")
                pyautogui.hotkey("ctrl", "l")
                await asyncio.sleep(0.2)
                pyautogui.write(query, interval=0.02)
                pyautogui.press("enter")

            elif action_name == "open_web_browser":
                import webbrowser
                await asyncio.to_thread(webbrowser.open, "about:blank")

            elif action_name == "navigate":
                import webbrowser
                url = args.get("url", "")
                if not url.startswith("http"):
                    url = "https://" + url
                await asyncio.to_thread(webbrowser.open, url)

            elif action_name == "open_url":
                import webbrowser
                url = args.get("url", "")
                if not url.startswith("http"):
                    url = "https://" + url
                await asyncio.to_thread(webbrowser.open, url)

            elif action_name == "launch_application":
                app_name = args.get("app_name", "").lower()

                if self.env_scanner and not self._is_app_launchable(app_name):
                    alternatives = self._get_alternatives_for(app_name)
                    alt = ", ".join(alternatives)
                    return f"APP_NOT_FOUND: {app_name}. Alternatives: {alt}"

                import subprocess
                import sys

                app_map = {
                    "chrome": "chrome",
                    "google chrome": "chrome",
                    "edge": "msedge",
                    "firefox": "firefox",
                    "notepad": "notepad",
                    "calculator": "calc",
                    "terminal": "cmd",
                    "explorer": "explorer",
                    "spotify": "spotify",
                    "discord": "discord",
                    "vlc": "vlc",
                }

                cmd = app_map.get(app_name, app_name)

                if sys.platform == "win32":
                    await asyncio.to_thread(
                        subprocess.Popen,
                        f'start "" "{cmd}"',
                        shell=True,
                    )
                elif sys.platform == "darwin":
                    await asyncio.to_thread(
                        subprocess.Popen,
                        ["open", "-a", cmd],
                    )
                else:
                    await asyncio.to_thread(
                        subprocess.Popen,
                        [cmd],
                    )
            else:
                print(f"⚠️ Unknown action: {action_name}")
                return f"unknown_action: {action_name}"

            return "success"

        except pyautogui.FailSafeException:
            return "failsafe_triggered"

        except Exception as e:
            print("Dispatcher Error:", e)
            return f"error: {str(e)}"

    def _scale_coords(self, x, y):
        if x is None or y is None:
            return 0, 0
        real_x = int((x / 1000) * self.screen_width)
        real_y = int((y / 1000) * self.screen_height)
        return real_x, real_y

    async def _request_confirmation(self, title, message):
        print("⚠️ SAFETY:", message)

        if not self.ui:
            return True

        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)

        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        ret = msg_box.exec()
        return ret == QMessageBox.StandardButton.Yes

    def _is_app_launchable(self, app_name):
        if not self.env_scanner:
            return True

        if self.env_scanner.is_app_installed(app_name):
            return True

        return False

    def _get_alternatives_for(self, app_name):
        if not self.env_scanner:
            return []

        capabilities = self.env_scanner.get_capabilities()
        alternatives = set()

        for apps in capabilities.values():
            for app in apps:
                alternatives.add(app)

        return sorted(alternatives)
