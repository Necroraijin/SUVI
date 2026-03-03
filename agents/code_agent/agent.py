"""Code Agent - Multi-language code intelligence agent."""

from typing import Optional
from agents.shared.agent_utils import GeminiAgent
from shared.suvi_types import AgentType, AgentCard, Task, AgentResult, AgentResultStatus
from shared.a2a import A2AServer


class CodeAgent(GeminiAgent, A2AServer):
    """Agent for code generation, refactoring, and debugging."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8003):
        GeminiAgent.__init__(self,
            agent_type=AgentType.CODE,
            system_prompt="""You are SUVI Code Agent, an expert code generation and debugging assistant.

Capabilities:
- Generate code in Python, TypeScript, Java, Go, Rust, SQL, Bash, Terraform
- Refactor and improve existing code
- Debug and fix code issues
- Complete partial code snippets
- Generate unit tests
- Explain code functionality

RAG: Use user's codebase context when available.
Always provide well-structured, production-ready code.
Include proper error handling and documentation.
Follow language-specific best practices.""",
            model_override="gemini-2.0-pro-001"
        )
        # Use pro model for highest code quality
        self.model = "gemini-2.0-pro-001"
        
        card = AgentCard(
            agent_id="suvi-code-agent",
            name="CodeAgent",
            description="Multi-language code intelligence agent.",
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
                agent_type=AgentType.CODE,
                task_id=task.id,
                status=AgentResultStatus.SUCCESS,
                output=output
            )
        except Exception as e:
            return AgentResult(
                agent_type=AgentType.CODE,
                task_id=task.id,
                status=AgentResultStatus.ERROR,
                error=str(e)
            )

    async def generate_code(
        self,
        language: str,
        description: str,
        framework: Optional[str] = None
    ) -> str:
        """Generate code based on description."""
        prompt = f"""Generate {language} code for the following:

Description: {description}
Framework: {framework or 'N/A'}

Provide:
1. Complete, working code
2. Brief explanation
3. Any required imports or dependencies"""
        return await self.generate(prompt)

    async def refactor_code(self, code: str, target_style: str = "clean") -> str:
        """Refactor existing code."""
        prompt = f"""Refactor the following code to be more {target_style}:

```{code}```

Provide:
1. Refactored code
2. List of changes made
3. Any improvements in performance or readability"""
        return await self.generate(prompt)

    async def debug_code(self, code: str, error: Optional[str] = None) -> str:
        """Debug code and fix issues."""
        prompt = f"""Debug the following code:

```{code}```

{'-' * 40}
Error message: {error or 'No specific error provided'}
{'-' * 40}

Provide:
1. Identified issues
2. Fixed code
3. Explanation of fixes"""
        return await self.generate(prompt)

    async def complete_code(self, code: str, language: str) -> str:
        """Complete partial code snippet."""
        prompt = f"""Complete the following {language} code snippet:

```{code}```

Provide the complete code with proper syntax."""
        return await self.generate(prompt)

    async def generate_tests(self, code: str, framework: str = "pytest") -> str:
        """Generate unit tests for code."""
        prompt = f"""Generate unit tests using {framework} for the following code:

```{code}```

Provide:
1. Test file content
2. Explanation of test coverage
3. How to run the tests"""
        return await self.generate(prompt)

    async def process_task(self, task: str, operation: str = "generate", **kwargs) -> str:
        """Process code task using Gemini Tool Binding."""
        tools = [
            self.generate_code,
            self.refactor_code,
            self.debug_code,
            self.complete_code,
            self.generate_tests
        ]
        
        prompt = f"User Request: {task}"
        return await self.generate(prompt, tools=tools)
