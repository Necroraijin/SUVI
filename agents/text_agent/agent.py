"""Text Agent - NLP and content intelligence agent."""

from typing import Optional
from agents.shared.agent_utils import GeminiAgent
from shared.suvi_types import AgentType, AgentCard, Task, AgentResult, AgentResultStatus
from shared.a2a import A2AServer


class TextAgent(GeminiAgent, A2AServer):
    """Agent for text processing: summarization, writing, translation."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8002):
        GeminiAgent.__init__(self,
            agent_type=AgentType.TEXT,
            system_prompt="""You are SUVI Text Agent, an expert in content creation and NLP.

Capabilities:
- Summarize long text into concise summaries
- Generate high-quality content (emails, articles, posts)
- Translate between 50+ languages
- Extract key information from documents
- Rewrite content in different tones (formal, casual, professional)

Always provide clear, engaging, and well-structured content.
When translating, maintain the original meaning and nuance.
When summarizing, capture the key points without losing important details."""
        )
        
        card = AgentCard(
            agent_id="suvi-text-agent",
            name="TextAgent",
            description="NLP and content intelligence agent.",
            url=f"http://{host}:{port}",
            provider={"name": "SUVI"},
            capabilities=[]
        )
        A2AServer.__init__(self, agent_card=card, host=host, port=port)

    async def execute_task(self, task: Task) -> Optional[AgentResult]:
        """A2A Protocol entry point for executing a task."""
        try:
            # We pass the user_input to our standard processing logic
            output = await self.process_task(task.user_input)
            
            return AgentResult(
                agent_type=AgentType.TEXT,
                task_id=task.id,
                status=AgentResultStatus.SUCCESS,
                output=output
            )
        except Exception as e:
            return AgentResult(
                agent_type=AgentType.TEXT,
                task_id=task.id,
                status=AgentResultStatus.ERROR,
                error=str(e)
            )

    async def summarize(self, text: str, max_words: int = 100) -> str:
        """Summarize text to specified word count."""
        prompt = f"""Summarize the following text in no more than {max_words} words:

{text}

Provide a clear, concise summary that captures the main points."""
        return await self.generate(prompt)

    async def translate(self, text: str, target_language: str) -> str:
        """Translate text to target language."""
        prompt = f"""Translate the following text to {target_language}:

{text}

Provide a natural translation that maintains the original meaning and nuance."""
        return await self.generate(prompt)

    async def rewrite(self, text: str, tone: str = "professional") -> str:
        """Rewrite text in specified tone."""
        prompt = f"""Rewrite the following text in a {tone} tone:

{text}

Maintain the original meaning while adjusting the tone and style."""
        return await self.generate(prompt)

    async def extract_key_points(self, text: str) -> str:
        """Extract key points from text."""
        prompt = f"""Extract the key points from the following text as a bulleted list:

{text}

List each key point on a separate line starting with a bullet character (-)."""
        return await self.generate(prompt)

    async def process_task(self, task: str, operation: str = "general", **kwargs) -> str:
        """Process text task using Gemini Tool Binding."""
        # We pass our native Python functions as tools directly to the Gemini SDK
        tools = [
            self.summarize,
            self.translate,
            self.rewrite,
            self.extract_key_points
        ]
        
        # If the user input is meant for a specific operation, they usually just provide text
        # Gemini will decide which tool to call based on the prompt.
        prompt = f"User Request: {task}"
        
        return await self.generate(prompt, tools=tools)
