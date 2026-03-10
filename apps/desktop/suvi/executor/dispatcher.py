import pyautogui
import asyncio
from PyQt6.QtWidgets import QMessageBox
from .permissions import RiskLevel, get_action_risk

class ActionDispatcher:
    """
    The secure gatekeeper for all physical computer actions.
    Wraps PyAutoGUI with safety checks and user confirmation dialogs.
    """
    def __init__(self, ui_widget=None):
        self.ui = ui_widget
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
            
            if action_name == "click_at":
                x, y = self._scale_coords(args.get("x", 0), args.get("y", 0))
                pyautogui.click(x, y)
                
            elif action_name == "right_click_at":
                x, y = self._scale_coords(args.get("x", 0), args.get("y", 0))
                pyautogui.rightClick(x, y)
                
            elif action_name == "double_click_at":
                x, y = self._scale_coords(args.get("x", 0), args.get("y", 0))
                pyautogui.doubleClick(x, y)
                
            elif action_name == "drag_to":
                start_x, start_y = self._scale_coords(args.get("start_x", 0), args.get("start_y", 0))
                end_x, end_y = self._scale_coords(args.get("end_x", 0), args.get("end_y", 0))
                pyautogui.moveTo(start_x, start_y)
                pyautogui.dragTo(end_x, end_y, duration=0.5)
                
            elif action_name == "type_text_at":
                # First click the target
                if "x" in args and "y" in args:
                    x, y = self._scale_coords(args["x"], args["y"])
                    pyautogui.click(x, y)
                    await asyncio.sleep(0.1)
                
                pyautogui.write(args.get("text", ""), interval=0.02)
                if args.get("press_enter"):
                    pyautogui.press("enter")
                    
            elif action_name == "press_key":
                key = args.get("key", "enter")
                pyautogui.press(key)
                
            elif action_name == "scroll_document":
                direction = args.get("direction", "down")
                amount = args.get("amount", 5)
                clicks = amount if direction == "up" else -amount
                pyautogui.scroll(clicks)
                
            elif action_name == "key_combination":
                keys = args.get("keys", [])
                pyautogui.hotkey(*keys)
                
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
