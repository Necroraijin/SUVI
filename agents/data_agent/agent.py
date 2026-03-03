"""Data Agent - Data analysis and visualization agent."""

from typing import Optional, Any
from agents.shared.agent_utils import GeminiAgent
from shared.suvi_types import AgentType, AgentCard, Task, AgentResult, AgentResultStatus
from shared.a2a import A2AServer


class DataAgent(GeminiAgent, A2AServer):
    """Agent for data analysis and visualization."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8007):
        GeminiAgent.__init__(self,
            agent_type=AgentType.DATA,
            system_prompt="""You are SUVI Data Agent, an expert in data analysis and visualization.

Capabilities:
- Analyze datasets and generate insights
- Create data visualizations (charts, graphs)
- Perform statistical analysis
- Query and analyze BigQuery data
- Generate CSV/Excel reports
- Create dashboards and summaries

Always provide accurate analysis with clear explanations.
Use appropriate visualizations for different data types.
Explain your methodology and assumptions.""",
            model_override="gemini-2.0-pro-001"
        )
        # Use pro model for complex data analysis
        self.model = "gemini-2.0-pro-001"
        
        card = AgentCard(
            agent_id="suvi-data-agent",
            name="DataAgent",
            description="Data analysis and visualization agent.",
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
                agent_type=AgentType.DATA,
                task_id=task.id,
                status=AgentResultStatus.SUCCESS,
                output=output
            )
        except Exception as e:
            return AgentResult(
                agent_type=AgentType.DATA,
                task_id=task.id,
                status=AgentResultStatus.ERROR,
                error=str(e)
            )

    async def analyze_data(self, data: str, analysis_type: str = "general") -> str:
        """Analyze provided data."""
        prompt = f"""Analyze the following data and provide insights:

Data:
{data}

Analysis type: {analysis_type}

Provide:
1. Summary statistics
2. Key patterns and trends
3. Any anomalies or outliers
4. Actionable insights"""
        return await self.generate(prompt)

    async def create_visualization(
        self,
        data: str,
        chart_type: str = "bar",
        x_axis: Optional[str] = None,
        y_axis: Optional[str] = None
    ) -> str:
        """Create a visualization specification."""
        prompt = f"""Create a {chart_type} chart for the following data:

Data:
{data}

X-axis: {x_axis or 'auto'}
Y-axis: {y_axis or 'auto'}

Describe the visualization that should be created, including:
1. Chart title
2. Axis labels
3. Color scheme
4. Any annotations or highlights"""
        return await self.generate(prompt)

    async def generate_report(self, data: str, report_type: str = "summary") -> str:
        """Generate a data report."""
        prompt = f"""Generate a {report_type} report for the following data:

Data:
{data}

Include:
1. Executive summary
2. Key metrics
3. Trends analysis
4. Recommendations"""
        return await self.generate(prompt)

    async def process_task(self, task: str, operation: str = "analyze", **kwargs) -> str:
        """Process data task using Gemini Tool Binding."""
        tools = [
            self.analyze_data,
            self.create_visualization,
            self.generate_report
        ]
        
        prompt = f"User Request: {task}"
        return await self.generate(prompt, tools=tools)
