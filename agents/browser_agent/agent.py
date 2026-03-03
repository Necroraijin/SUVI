"""Browser Agent - Web navigation and browser automation agent."""

from typing import Optional
from agents.shared.agent_utils import GeminiAgent
from shared.suvi_types import AgentType, AgentCard, Task, AgentResult, AgentResultStatus
from shared.a2a import A2AServer


class BrowserAgent(GeminiAgent, A2AServer):
    """Agent for web browsing and automation."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8004):
        GeminiAgent.__init__(self,
            agent_type=AgentType.BROWSER,
            system_prompt="""You are SUVI Browser Agent, expert in web navigation and automation.

Capabilities:
- Navigate to websites and extract content
- Fill forms and interact with web elements
- Perform web research and data extraction
- Automate repetitive browser tasks
- Take screenshots (via desktop executor)

Always verify information from reliable sources.
Provide accurate citations for factual claims.
Respect website terms of service.""",
            model_override="gemini-2.0-flash-001"
        )
        
        card = AgentCard(
            agent_id="suvi-browser-agent",
            name="BrowserAgent",
            description="Web navigation and browser automation agent.",
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
                agent_type=AgentType.BROWSER,
                task_id=task.id,
                status=AgentResultStatus.SUCCESS,
                output=output
            )
        except Exception as e:
            return AgentResult(
                agent_type=AgentType.BROWSER,
                task_id=task.id,
                status=AgentResultStatus.ERROR,
                error=str(e)
            )

    async def navigate_to(self, url: str) -> str:
        """Navigate to a URL."""
        prompt = f"""Navigate to: {url}

Verify the page loaded successfully and provide:
1. Page title
2. Main heading
3. A brief summary of the page content"""
        return await self.generate(prompt)

    async def extract_content(self, url: str, selectors: Optional[list] = None) -> str:
        """Extract content from a webpage."""
        prompt = f"""Extract content from: {url}

{'-' * 40}
Target selectors: {selectors or 'body'}
{'-' * 40}

Extract:
1. Main heading
2. Key paragraphs
3. Any relevant data tables or lists
4. Links to related pages"""
        return await self.generate(prompt)

    async def fill_form(self, url: str, form_data: dict) -> str:
        """Fill and submit a web form."""
        prompt = f"""Navigate to: {url}

Fill the following form fields:
{form_data}

Submit the form and report:
1. Whether submission was successful
2. Any error messages
3. Resulting page content"""
        return await self.generate(prompt)

    async def research_topic(self, topic: str) -> str:
        """Research a topic by browsing multiple sources."""
        prompt = f"""Research the following topic comprehensively:

{topic}

Browse multiple sources and provide:
1. Overview of the topic
2. Key facts and statistics
3. Different perspectives
4. Sources with links"""
        return await self.generate(prompt)

    async def process_task(self, task: str, operation: str = "navigate", **kwargs) -> str:
        """Process browser task using Gemini Tool Binding."""
        tools = [
            self.navigate_to,
            self.extract_content,
            self.fill_form,
            self.research_topic
        ]
        
        prompt = f"User Request: {task}"
        return await self.generate(prompt, tools=tools)
