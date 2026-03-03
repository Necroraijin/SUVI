"""A2A Protocol Implementation - Google Agent-to-Agent Communication Protocol."""

import asyncio
import json
from typing import Any, Optional, AsyncGenerator
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import aiohttp

from shared.suvi_types import AgentCard, AgentCapability, Task, TaskStatus, AgentResult, AgentType


class A2AMessageType(str, Enum):
    """A2A message types as per protocol specification."""
    REQUEST = "request"
    RESPONSE = "response"
    TASK_SUBMISSION = "task/submission"
    TASK_STATUS_UPDATE = "task/statusUpdate"
    TASK_PUSH_NOTIFICATION = "task/pushNotification"
    AGENT_CARD = "agentCard"
    ERROR = "error"


class A2ATaskState(str, Enum):
    """A2A task states."""
    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class A2AMessage:
    """A2A protocol message envelope."""
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    method: Optional[str] = None
    params: dict[str, Any] = field(default_factory=dict)
    result: Optional[Any] = None
    error: Optional[dict[str, Any]] = None

    def to_json(self) -> str:
        """Serialize message to JSON."""
        data = {"jsonrpc": self.jsonrpc}
        if self.id:
            data["id"] = self.id
        if self.method:
            data["method"] = self.method
        if self.params:
            data["params"] = self.params
        if self.result is not None:
            data["result"] = self.result
        if self.error:
            data["error"] = self.error
        return json.dumps(data)

    @classmethod
    def from_json(cls, json_str: str) -> "A2AMessage":
        """Deserialize message from JSON."""
        data = json.loads(json_str)
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            id=data.get("id"),
            method=data.get("method"),
            params=data.get("params", {}),
            result=data.get("result"),
            error=data.get("error")
        )


class A2AClient:
    """A2A Protocol HTTP Client for agent-to-agent communication."""

    def __init__(
        self,
        agent_url: str,
        agent_card: Optional[AgentCard] = None,
        timeout: float = 30.0,
        auth_token: Optional[str] = None
    ):
        """
        Initialize A2A client for an agent.

        Args:
            agent_url: Base URL of the agent server
            agent_card: Agent capability card (optional, can be fetched)
            timeout: Request timeout in seconds
            auth_token: Optional authentication token
        """
        self.agent_url = agent_url.rstrip("/")
        self.agent_card = agent_card
        self.timeout = timeout
        self.auth_token = auth_token
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self):
        """Establish HTTP session."""
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        self._session = aiohttp.ClientSession(
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )

    async def disconnect(self):
        """Close HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None

    async def get_agent_card(self) -> AgentCard:
        """Fetch agent card from the agent server."""
        if self.agent_card:
            return self.agent_card

        async with self._session.get(f"{self.agent_url}/agentCard") as resp:
            resp.raise_for_status()
            data = await resp.json()
            return AgentCard(**data)

    async def send_task(
        self,
        task: Task,
        session_id: Optional[str] = None
    ) -> A2AMessage:
        """
        Send a task to the agent (non-streaming).

        Args:
            task: Task to execute
            session_id: Optional session identifier

        Returns:
            A2A message with task result
        """
        message = A2AMessage(
            id=f"msg_{datetime.now().timestamp()}",
            method="tasks/send",
            params={
                "task": task.model_dump(),
                "sessionId": session_id
            }
        )

        async with self._session.post(
            f"{self.agent_url}/rpc",
            data=message.to_json(),
            headers={"Content-Type": "application/json"}
        ) as resp:
            resp.raise_for_status()
            result = await resp.text()
            return A2AMessage.from_json(result)

    async def send_task_streaming(
        self,
        task: Task,
        session_id: Optional[str] = None
    ) -> AsyncGenerator[A2AMessage, None]:
        """
        Send a task to the agent with streaming responses.

        Args:
            task: Task to execute
            session_id: Optional session identifier

        Yields:
            A2A messages as task progresses
        """
        async with self._session.post(
            f"{self.agent_url}/rpc",
            data=A2AMessage(
                id=f"msg_{datetime.now().timestamp()}",
                method="tasks/sendSubscribe",
                params={
                    "task": task.model_dump(),
                    "sessionId": session_id
                }
            ).to_json(),
            headers={"Content-Type": "application/json"}
        ) as resp:
            resp.raise_for_status()
            async for line in resp.content:
                if line.strip():
                    yield A2AMessage.from_json(line.decode())

    async def get_task_status(self, task_id: str) -> A2AMessage:
        """Get the status of a submitted task."""
        message = A2AMessage(
            id=f"msg_{datetime.now().timestamp()}",
            method="tasks/get",
            params={"taskId": task_id}
        )

        async with self._session.post(
            f"{self.agent_url}/rpc",
            data=message.to_json(),
            headers={"Content-Type": "application/json"}
        ) as resp:
            resp.raise_for_status()
            return A2AMessage.from_json(await resp.text())

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task."""
        message = A2AMessage(
            id=f"msg_{datetime.now().timestamp()}",
            method="tasks/cancel",
            params={"taskId": task_id}
        )

        async with self._session.post(
            f"{self.agent_url}/rpc",
            data=message.to_json(),
            headers={"Content-Type": "application/json"}
        ) as resp:
            return resp.status == 200


class A2AServer:
    """A2A Protocol Server base class for hosting agents."""

    def __init__(
        self,
        agent_card: AgentCard,
        host: str = "0.0.0.0",
        port: int = 8000
    ):
        """
        Initialize A2A server.

        Args:
            agent_card: Agent capability card
            host: Server host
            port: Server port
        """
        self.agent_card = agent_card
        self.host = host
        self.port = port
        self._tasks: dict[str, Task] = {}
        self._callbacks: dict[str, asyncio.Queue] = {}

    async def handle_message(self, message: A2AMessage) -> A2AMessage:
        """Handle incoming A2A message and route to appropriate handler."""
        try:
            if message.method == "tasks/send":
                return await self._handle_send_task(message)
            elif message.method == "tasks/sendSubscribe":
                return await self._handle_send_task_streaming(message)
            elif message.method == "tasks/get":
                return await self._handle_get_task(message)
            elif message.method == "tasks/cancel":
                return await self._handle_cancel_task(message)
            elif message.method == "agentCard/get":
                return A2AMessage(
                    id=message.id,
                    result=self.agent_card.model_dump()
                )
            else:
                return A2AMessage(
                    id=message.id,
                    error={
                        "code": -32601,
                        "message": f"Method not found: {message.method}"
                    }
                )
        except Exception as e:
            return A2AMessage(
                id=message.id,
                error={
                    "code": -32000,
                    "message": str(e)
                }
            )

    async def _handle_send_task(self, message: A2AMessage) -> A2AMessage:
        """Handle non-streaming task submission."""
        task_data = message.params.get("task", {})
        task = Task(**task_data)

        self._tasks[task.id] = task
        result = await self.execute_task(task)

        return A2AMessage(
            id=message.id,
            result={
                "taskId": task.id,
                "state": A2ATaskState.COMPLETED.value,
                "result": result.model_dump() if result else None
            }
        )

    async def _handle_send_task_streaming(self, message: A2AMessage) -> A2AMessage:
        """Handle streaming task submission."""
        task_data = message.params.get("task", {})
        task = Task(**task_data)

        self._tasks[task.id] = task
        queue = asyncio.Queue()
        self._callbacks[task.id] = queue

        asyncio.create_task(self._execute_task_streaming(task, queue))

        return A2AMessage(
            id=message.id,
            result={
                "taskId": task.id,
                "state": A2ATaskState.SUBMITTED.value
            }
        )

    async def _handle_get_task(self, message: A2AMessage) -> A2AMessage:
        """Handle task status query."""
        task_id = message.params.get("taskId")
        task = self._tasks.get(task_id)

        if not task:
            return A2AMessage(
                id=message.id,
                error={"code": -32001, "message": "Task not found"}
            )

        return A2AMessage(
            id=message.id,
            result={
                "taskId": task.id,
                "state": task.status.value,
                "task": task.model_dump()
            }
        )

    async def _handle_cancel_task(self, message: A2AMessage) -> A2AMessage:
        """Handle task cancellation."""
        task_id = message.params.get("taskId")
        task = self._tasks.get(task_id)

        if not task:
            return A2AMessage(
                id=message.id,
                error={"code": -32001, "message": "Task not found"}
            )

        task.status = TaskStatus.CANCELLED

        return A2AMessage(
            id=message.id,
            result={"taskId": task.id, "state": A2ATaskState.CANCELLED.value}
        )

    async def _execute_task_streaming(self, task: Task, queue: asyncio.Queue):
        """Execute task and stream results."""
        try:
            await queue.put(A2AMessage(
                method="task/statusUpdate",
                params={
                    "taskId": task.id,
                    "state": A2ATaskState.WORKING.value
                }
            ))

            result = await self.execute_task(task)

            await queue.put(A2AMessage(
                method="task/statusUpdate",
                params={
                    "taskId": task.id,
                    "state": A2ATaskState.COMPLETED.value,
                    "result": result.model_dump() if result else None
                }
            ))
        except Exception as e:
            await queue.put(A2AMessage(
                method="task/statusUpdate",
                params={
                    "taskId": task.id,
                    "state": A2ATaskState.FAILED.value,
                    "error": str(e)
                }
            ))
        finally:
            if task.id in self._callbacks:
                del self._callbacks[task.id]

    async def execute_task(self, task: Task) -> Optional[AgentResult]:
        """
        Execute the task. Override this in subclasses.

        Args:
            task: Task to execute

        Returns:
            Agent result
        """
        raise NotImplementedError("Subclasses must implement execute_task")

    async def start_server(self):
        """Start the A2A HTTP server."""
        from aiohttp import web

        app = web.Application()
        app.router.add_post("/rpc", self._handle_rpc)
        app.router.add_get("/agentCard", self._handle_agent_card)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()

        return runner

    async def _handle_rpc(self, request: web.Request) -> web.Response:
        """Handle RPC endpoint."""
        message = A2AMessage.from_json(await request.text())
        response = await self.handle_message(message)
        return web.json_response(
            json.loads(response.to_json()),
            status=200
        )

    async def _handle_agent_card(self, request: web.Request) -> web.Response:
        """Handle agent card endpoint."""
        return web.json_response(self.agent_card.model_dump())
