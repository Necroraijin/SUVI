from typing import Optional
from google import genai
from google.genai import types

class OrchestratorService:
    """
    SUVI's central reasoning engine.

    Responsibilities:
    - Task classification
    - Complex task planning
    - Coding assistance
    - Research assistance
    """

    MODEL_ID = "gemini-2.5-pro"

    def __init__(self, client: genai.Client):
        self.client = client

    # ---------------------------------------------------------
    # TASK CLASSIFIER
    # ---------------------------------------------------------
    async def classify_intent(self, user_input: str) -> str:
        """
        Determine which agent should handle the task.
        """
        prompt = f"""
Classify the user request into ONE category.

User request:
{user_input}

Categories:
desktop → controlling computer or apps
coding → programming help
research → information or questions

Respond with ONLY one word:
desktop
coding
research
"""
        try:
            response = await self.client.aio.models.generate_content(
                model=self.MODEL_ID,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0
                )
            )
            result = response.text.strip().lower()
            if "coding" in result:
                return "coding"
            if "research" in result:
                return "research"
            return "desktop"
        except Exception:
            return "desktop"

    # ---------------------------------------------------------
    # CODING AGENT
    # ---------------------------------------------------------
    async def generate_coding_solution(self, prompt: str, language: Optional[str] = None) -> str:
        system_instruction = f"""
You are SUVI's coding expert.
Provide clean, correct, well documented code.
Preferred language: {language if language else "any"}
"""
        try:
            response = await self.client.aio.models.generate_content(
                model=self.MODEL_ID,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2
                )
            )
            return response.text
        except Exception as e:
            return f"Coding agent error: {str(e)}"

    # ---------------------------------------------------------
    # RESEARCH AGENT
    # ---------------------------------------------------------
    async def perform_research(self, query: str) -> str:
        system_instruction = """
You are SUVI's research assistant.
Provide accurate factual answers.
Be concise but informative.
"""
        try:
            response = await self.client.aio.models.generate_content(
                model=self.MODEL_ID,
                contents=query,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2
                )
            )
            return response.text
        except Exception as e:
            return f"Research agent error: {str(e)}"

    # ---------------------------------------------------------
    # DESKTOP TASK PLANNER
    # ---------------------------------------------------------
    async def plan_complex_task(self, intent: str, env_context: str = "") -> str:
        env_section = f"""
CURRENT USER ENVIRONMENT
{env_context}
If an application is not installed, use the browser alternative.
""" if env_context else ""

        prompt = f"""
You are SUVI's automation planner.
Convert the user request into a clear step-by-step plan for a desktop automation agent.

{env_section}

USER INTENT:
{intent}

Rules:
1. Output ONLY numbered steps.
2. Do NOT explain anything.
3. Do NOT provide options.
4. Use realistic UI actions.
"""
        try:
            response = await self.client.aio.models.generate_content(
                model=self.MODEL_ID,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1
                )
            )
            return response.text
        except Exception:
            return intent