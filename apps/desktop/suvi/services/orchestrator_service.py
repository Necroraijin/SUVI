import asyncio
from typing import Optional
from google import genai
from google.genai import types

class OrchestratorService:
    """
    The 'Brain' of SUVI. Uses Gemini 2.5 Pro to reason about complex tasks
    and provide guidance or direct solutions for specialized domains.
    """
    
    # Using Gemini 2.5 Pro as the Brain
    MODEL_ID = "gemini-3.1-pro-preview"

    def __init__(self, client: genai.Client):
        self.client = client

    async def generate_coding_solution(self, prompt: str, language: Optional[str] = None) -> str:
        """Invokes the Pro model to solve programming tasks."""
        system_instruction = f"""You are SUVI's Coder Agent. You are a world-class software engineer.
Your goal is to provide clean, efficient, and well-documented code or bug fixes.
User language preference: {language if language else 'Any'}
Provide the solution clearly and concisely."""

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
            return f"Error in Coder Agent: {str(e)}"

    async def perform_research(self, query: str) -> str:
        """Uses the Pro model with web search capabilities to answer complex questions."""
        system_instruction = """You are SUVI's Research Agent.
You have access to vast knowledge and search tools.
Provide accurate, factual, and synthesized information based on the user's query."""

        try:
            # Note: We enable Google Search tool for the Pro model here
            response = await self.client.aio.models.generate_content(
                model=self.MODEL_ID,
                contents=query,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    tools=[types.Tool(google_search=types.GoogleSearchRetrieval())],
                    temperature=0.0
                )
            )
            return response.text
        except Exception as e:
            return f"Error in Research Agent: {str(e)}"

    async def plan_complex_task(self, intent: str, env_context: str = "") -> str:
        """
        Breaks down a complex user intent into a step-by-step plan
        that the Desktop Agent can follow.
        """
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
                model=self.MODEL_ID,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1
                )
            )
            return response.text
        except Exception as e:
            return intent # Fallback to original intent if planning fails
