"""Agent Shared Utilities - Common code for all ADK agents."""

import os
import json
from typing import Optional, Any
from pathlib import Path

from google import genai
from google.genai import types

from shared.suvi_types import AgentCard, AgentCapability, AgentType


# GCP Configuration
GCP_PROJECT = os.environ.get("GCP_PROJECT", "suvi-project")
GCP_LOCATION = os.environ.get("GCP_LOCATION", "us-central1")


def get_gemini_client():
    """Initialize Gemini client with Vertex AI."""
    return genai.Client(
        vertexai=True,
        project=GCP_PROJECT,
        location=GCP_LOCATION
    )


def get_gemini_model(model_name: str = "gemini-2.0-flash-001") -> Any:
    """Get configured Gemini model."""
    client = get_gemini_client()
    return client.models


class AgentConfig:
    """Configuration for SUVI agents."""

    def __init__(self, agent_type: AgentType):
        self.agent_type = agent_type
        self.project = GCP_PROJECT
        self.location = GCP_LOCATION
        self.model = "gemini-2.0-flash-001"
        self.max_output_tokens = 2048
        self.temperature = 0.7
        self.top_p = 0.95
        self.top_k = 40

    @property
    def agent_id(self) -> str:
        return f"suvi-{self.agent_type.value}-agent"

    @property
    def endpoint(self) -> str:
        return f"https://{self.project}-{self.location}.run.app/agents/{self.agent_type.value}"


class GeminiAgent:
    """Base class for Gemini-powered agents."""

    def __init__(self, agent_type: AgentType, system_prompt: str = ""):
        self.config = AgentConfig(agent_type)
        self.agent_type = agent_type
        self.system_prompt = system_prompt or self._get_default_prompt()
        self.client = get_gemini_client()
        self.model = self.config.model

    def _get_default_prompt(self) -> str:
        """Get default system prompt based on agent type."""
        prompts = {
            AgentType.ORCHESTRATOR: """You are SUVI Orchestrator, the master planner and router.
You analyze user requests and route them to the appropriate sub-agent.
Available agents: code, text, browser, search, memory, email, data.
Always provide clear, concise responses.""",

            AgentType.CODE: """You are SUVI Code Agent, an expert code generation and debugging assistant.
You can write, refactor, and debug code in Python, TypeScript, Java, Go, Rust, SQL, and more.
Always provide well-structured, production-ready code.""",

            AgentType.TEXT: """You are SUVI Text Agent, an expert in content creation and NLP.
You can summarize, write, translate, and edit text in 50+ languages.
Always provide clear, engaging content.""",

            AgentType.BROWSER: """You are SUVI Browser Agent, expert in web navigation and automation.
You can browse websites, extract content, and automate browser interactions.
Always provide accurate information from web sources.""",

            AgentType.SEARCH: """You are SUVI Search Agent, expert in information retrieval.
You can search the web and verify facts using Google grounding.
Always provide accurate, sourced information.""",

            AgentType.MEMORY: """You are SUVI Memory Agent, managing persistent user context.
You store and recall relevant information from the user's history.
Always maintain context across conversations.""",

            AgentType.EMAIL: """You are SUVI Email Agent, expert in email composition.
You can draft, send, and manage emails via Gmail.
Always professional and concise.""",

            AgentType.DATA: """You are SUVI Data Agent, expert in data analysis.
You can analyze data, generate insights, and create visualizations.
Always provide accurate analysis with clear explanations.""",
        }
        return prompts.get(self.agent_type, f"You are SUVI {self.agent_type.value} agent.")

    async def generate(self, user_input: str, context: Optional[dict] = None, tools: Optional[list] = None) -> str:
        """Generate response using Gemini, with optional tool support."""
        contents = [types.Content(role="user", parts=[types.Part(text=user_input)])]

        if self.system_prompt:
            system_instruction = types.Content(
                role="system",
                parts=[types.Part(text=self.system_prompt)]
            )
        else:
            system_instruction = None

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            max_output_tokens=self.config.max_output_tokens,
            tools=tools
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=config
        )

        # If the model decided to call a tool, handle it (basic manual handling)
        if response.function_calls:
            results = []
            for call in response.function_calls:
                # Find the matching tool in our tools list
                func = next((t for t in tools if getattr(t, '__name__', '') == call.name), None)
                if func:
                    # Execute the function (handling async if needed)
                    import inspect
                    kwargs = {k: v for k, v in call.args.items()}
                    try:
                        if inspect.iscoroutinefunction(func):
                            res = await func(**kwargs)
                        else:
                            res = func(**kwargs)
                        results.append(str(res))
                    except Exception as e:
                        results.append(f"Error executing {call.name}: {e}")
                else:
                    results.append(f"Function {call.name} not found.")
            
            # For simplicity in this Hackathon skeleton, we just return the tool execution result
            # A full implementation would pass this back to the model as a tool response.
            return "\n".join(results)

        return response.text if hasattr(response, 'text') else str(response)

    async def generate_stream(self, user_input: str):
        """Generate streaming response using Gemini."""
        contents = [types.Content(role="user", parts=[types.Part(text=user_input)])]

        if self.system_prompt:
            system_instruction = types.Content(
                role="system",
                parts=[types.Part(text=self.system_prompt)]
            )
        else:
            system_instruction = None

        response = self.client.models.generate_content_stream(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                max_output_tokens=self.config.max_output_tokens,
            )
        )

        for chunk in response:
            yield chunk.text if hasattr(chunk, 'text') else str(chunk)
