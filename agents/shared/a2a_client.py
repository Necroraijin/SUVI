import asyncio
from typing import Optional, Dict, Any
from shared.a2a import A2AClient as BaseA2AClient, A2AMessage
from shared.suvi_types import Task, AgentResult, AgentResultStatus, TaskStatus
from tenacity import retry, stop_after_attempt, wait_exponential

class A2AClient:
    """Refactored A2A Client that uses the core A2A protocol implementation."""
    
    def __init__(self, agent_name: str, agent_url: Optional[str] = None):
        self.agent_name = agent_name
        # Default mapping for local development if no URL is provided
        self.agent_url = agent_url or f"http://localhost:8001/{agent_name.lower()}"
        self._client = BaseA2AClient(agent_url=self.agent_url)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def _send_task_with_retry(self, task: Task) -> A2AMessage:
        """Internal helper to execute the network call with exponential backoff."""
        async with self._client as client:
            return await client.send_task(task)

    async def send_task(self, target_agent: str, user_input: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        """
        Sends a task to another agent using the real A2A protocol.
        Wraps the A2A message into an AgentResult for compatibility.
        """
        print(f"[{self.agent_name} -> {target_agent}] Dispatching task: {user_input}")
        
        # 1. Create a proper Task object
        task = Task(
            user_input=user_input,
            memory_context=context or {}
        )
        
        try:
            # 2. Use the real A2A protocol client with retry logic
            response: A2AMessage = await self._send_task_with_retry(task)
            
            if response.error:
                    return AgentResult(
                        agent_type=target_agent,
                        task_id=task.id,
                        status=AgentResultStatus.ERROR,
                        error=response.error.get("message", "Unknown A2A error")
                    )
                
                # 3. Extract the result from the A2A response
                # The protocol returns the result in params or result depending on the method
                result_data = response.result
                
                # Convert result_data back to AgentResult
                if isinstance(result_data, dict) and "result" in result_data:
                    # The A2AServer wraps results in a dict with 'result' key
                    inner_result = result_data["result"]
                    if isinstance(inner_result, dict):
                        return AgentResult(**inner_result)
                    else:
                        return AgentResult(
                            agent_type=target_agent,
                            task_id=task.id,
                            status=AgentResultStatus.SUCCESS,
                            output=str(inner_result)
                        )
                
                return AgentResult(
                    agent_type=target_agent,
                    task_id=task.id,
                    status=AgentResultStatus.SUCCESS,
                    output=str(result_data)
                )

        except Exception as e:
            print(f"[A2A Error] Failed to communicate with {target_agent}: {e}")
            return AgentResult(
                agent_type=target_agent,
                task_id=task.id,
                status=AgentResultStatus.ERROR,
                error=str(e)
            )
