import os
from google import genai
from google.genai import types

from .tools.computer_use_tool import computer_use_tool
from .tools.memory_tool import memory_tool
from .tools.web_search_tool import web_search_tool
from .system_prompt import ORCHESTRATOR_SYSTEM_PROMPT



def get_orchestrator_config():
    return {
        "model": "gemini-3.1-pro-preview",
        "system_instruction": ORCHESTRATOR_SYSTEM_PROMPT,
        "tools": [
            computer_use_tool,
            memory_tool.search,
            web_search_tool
        ]
    }


