import os
from google import genai
from google.genai import types

class OrchestratorProxy:
    """
    Proxies calls to the Vertex AI Orchestrator Agent.
    This runs on the Gateway to keep API keys and models secure.
    """
    def __init__(self, api_key: str):
        self.client = genai.Client(
            api_key=api_key,
            http_options={'api_version': 'v1alpha'}
        )
        self.model_id = "gemini-3.1-pro-preview"

    async def get_plan(self, intent: str, env_context: str = "") -> str:
        """Asks the orchestrator to break down a complex task."""
        # Build the prompt with environment context
        env_section = f"""
CURRENT USER ENVIRONMENT:
{env_context}

IMPORTANT: Use the above environment info to create a realistic plan.
If an app is NOT in the installed apps list, either:
- Use an alternative app that's installed, OR
- Use the default browser to access a web-based version

""" if env_context else ""

        prompt = f"""You are the SUVI Orchestrator.
Your job is to take a vague user intent and break it down into an EXACT, linear step-by-step plan for a Computer Use AI Automation Agent operating a Windows desktop.
{env_section}
USER INTENT: {intent}

RULES:
1. Provide ONLY the step-by-step plan. No introductory or concluding text (e.g. do not say "Here is a breakdown").
2. DO NOT provide options or alternative scenarios (e.g. NO "Scenario A" vs "Scenario B"). Choose the most direct path and stick to it.
3. Address the plan directly to the execution agent.
4. Keep the steps sequential and specific (e.g., "1. Launch Chrome.", "2. Click the address bar and navigate to YouTube").
5. NEVER assume an app is installed unless it's listed in the environment info above."""
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_id,
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"Error: {e}"

    async def get_code(self, prompt: str) -> str:
        """Calls the coder agent logic."""
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_id,
                contents=f"Solve this coding problem: {prompt}",
                config=types.GenerateContentConfig(
                    system_instruction="You are SUVI's Coder Agent."
                )
            )
            return response.text
        except Exception as e:
            return f"Error: {e}"
