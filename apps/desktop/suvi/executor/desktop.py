import pyautogui
import asyncio
from apps.desktop.suvi.executor.kill_switch import KillSwitch

class DesktopExecutor:
    """Translates agent commands into physical OS inputs."""
    
    def __init__(self):
        # PyAutoGUI Fail-Safe: Slamming your mouse into any corner of the screen 
        # will instantly abort the script and throw an exception.
        pyautogui.FAILSAFE = True
        
        # Make movements slightly more natural, not instant teleports
        pyautogui.MINIMUM_DURATION = 0.1 

    async def click(self, x: int, y: int):
        if KillSwitch.is_active(): return "Aborted by Kill Switch."
        
        # Yield to the event loop briefly so UI doesn't freeze
        await asyncio.sleep(0) 
        pyautogui.click(x=x, y=y)
        return f"Successfully clicked coordinates ({x}, {y})."

    async def type_text(self, text: str):
        if KillSwitch.is_active(): return "Aborted by Kill Switch."
        
        await asyncio.sleep(0)
        # Type with a slight delay between keystrokes to mimic human input
        pyautogui.write(text, interval=0.02)
        return "Text typing completed."

    async def press_hotkey(self, keys: list[str]):
        if KillSwitch.is_active(): return "Aborted by Kill Switch."
        
        await asyncio.sleep(0)
        pyautogui.hotkey(*keys)
        return f"Executed hotkey: {'+'.join(keys)}."