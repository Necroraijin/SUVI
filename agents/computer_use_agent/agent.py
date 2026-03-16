from google.genai import types
from .system_prompt import COMPUTER_USE_SYSTEM_PROMPT

class ComputerUseAgent:
    """
    Sub-agent specialized for vision-based task execution on the desktop.
    Can be called by the SUVI Orchestrator as a tool.
    """
    MODEL_ID = "gemini-2.5-computer-use-preview-10-2025"

    def __init__(self, client):
        self.client = client
        self.system_instruction = COMPUTER_USE_SYSTEM_PROMPT

    def get_config(self):
        """Configuration for Vertex AI Agent Engine."""
        return {
            "model": self.MODEL_ID,
            "system_instruction": self.system_instruction,
            "tools": [
                "click_at", "right_click_at", "double_click_at", 
                "drag_to", "type_text_at", "press_key", "scroll_document",
                "voice_confirmation"
            ]
        }
