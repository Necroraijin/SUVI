import asyncio
from typing import Optional
from google import genai
from google.genai import types

class OrchestratorService:
    """
    The 'Brain' of SUVI. Uses Gemini 2.5 Pro to reason about complex tasks
    and provide guidance or direct solutions for specialized domains.
    """
    
    # Using 1.5 Flash to avoid free-tier 429 quota exhaustion
    MODEL_ID = "gemini-2.5-pro-preview-06-05"

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

    async def plan_complex_task(self, intent: str) -> str:
        """
        Breaks down a complex user intent into a step-by-step plan 
        that the Desktop Agent can follow.
        """
        prompt = f"""Break down this complex desktop task into simple, sequential steps for a UI automation agent:
Task: {intent}

Provide the plan as a numbered list. Be very specific about UI elements."""

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
