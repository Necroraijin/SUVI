import os
from google import genai
from google.genai import types
# Note: Google ADK (Agent Development Kit) is used for high-level agent orchestration.
# However, the direct 'google-adk' package might have specific import paths.
# We will implement the Orchestrator logic using the GenAI SDK's Agent capabilities
# which is the underlying engine for Vertex AI Agents.

from .tools.computer_use_tool import computer_use_tool
from .tools.memory_tool import memory_tool
from .tools.web_search_tool import web_search_tool
from .system_prompt import ORCHESTRATOR_SYSTEM_PROMPT

# In Day 3, we define the Orchestrator that will live on Vertex AI.
# It uses Gemini 2.5 Pro for complex reasoning.

def get_orchestrator_config():
    return {
        "model": "gemini-2.5-pro-preview-06-05",
        "system_instruction": ORCHESTRATOR_SYSTEM_PROMPT,
        "tools": [
            computer_use_tool,
            memory_tool.search,
            web_search_tool
        ]
    }

# This file will be used by the deployment script in Day 3.
