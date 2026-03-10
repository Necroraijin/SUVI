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
        # Using 1.5 Flash here for planning because it has a massive 15 RPM free tier limit
        # This prevents the 429 RESOURCE_EXHAUSTED errors that happen with 2.5 on free tier.
        self.model_id = "gemini-1.5-flash"

    async def get_plan(self, intent: str) -> str:
        """Asks the orchestrator to break down a complex task."""
        prompt = f"Break down this desktop task into steps: {intent}"
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
