"""Search Agent - Web search and information retrieval with grounding."""

from typing import Optional
from agents.shared.agent_utils import GeminiAgent
from shared.suvi_types import AgentType, AgentCard, Task, AgentResult, AgentResultStatus
from shared.a2a import A2AServer


class SearchAgent(GeminiAgent, A2AServer):
    """Agent for web search and fact verification."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8005):
        GeminiAgent.__init__(self,
            agent_type=AgentType.SEARCH,
            system_prompt="""You are SUVI Search Agent, an expert in information retrieval and fact verification.

Capabilities:
- Search the web for current and accurate information
- Verify facts using Google grounding
- Provide sourced answers with citations
- Compare and contrast information from multiple sources
- Stay up-to-date with current events

Always provide accurate, well-sourced information.
Cite your sources when providing factual claims.
If information is uncertain, clearly indicate so."""
        )

        card = AgentCard(
            agent_id="suvi-search-agent",
            name="SearchAgent",
            description="Web search and information retrieval agent.",
            url=f"http://{host}:{port}",
            provider={"name": "SUVI"},
            capabilities=[]
        )
        A2AServer.__init__(self, agent_card=card, host=host, port=port)

    async def execute_task(self, task: Task) -> Optional[AgentResult]:
        """A2A Protocol entry point for executing a task."""
        try:
            output = await self.process_task(task.user_input)
            
            return AgentResult(
                agent_type=AgentType.SEARCH,
                task_id=task.id,
                status=AgentResultStatus.SUCCESS,
                output=output
            )
        except Exception as e:
            return AgentResult(
                agent_type=AgentType.SEARCH,
                task_id=task.id,
                status=AgentResultStatus.ERROR,
                error=str(e)
            )

    async def search(self, query: str, num_results: int = 5) -> str:
        """Search the web for information."""
        prompt = f"""Search for information about: {query}

Provide {num_results} relevant results with brief descriptions and sources."""
        return await self.generate(prompt)

    async def verify_fact(self, fact: str) -> str:
        """Verify a fact using web grounding."""
        prompt = f"""Verify the following fact by checking reliable sources:

"{fact}"

Provide:
1. Whether the fact is TRUE, FALSE, or PARTIALLY TRUE
2. Source citations supporting your assessment
3. Any additional context or nuance"""
        return await self.generate(prompt)

    async def get_comparison(self, item1: str, item2: str) -> str:
        """Compare two items."""
        prompt = f"""Compare and contrast the following:

Item 1: {item1}
Item 2: {item2}

Provide a balanced comparison covering similarities, differences, pros, and cons."""
        return await self.generate(prompt)

    async def process_task(self, task: str, operation: str = "search", **kwargs) -> str:
        """Process search task using Gemini Tool Binding."""
        tools = [
            self.search,
            self.verify_fact,
            self.get_comparison
        ]
        
        prompt = f"User Request: {task}"
        return await self.generate(prompt, tools=tools)
