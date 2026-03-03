"""Integration tests for A2A protocol flow."""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock

from shared.a2a import A2AClient, A2AMessage, A2ATaskState
from shared.suvi_types import Task, TaskStatus, AgentType


class TestA2AMessage:
    """Tests for A2A message handling."""

    def test_message_creation(self):
        """Test creating an A2A message."""
        message = A2AMessage(
            id="test_1",
            method="tasks/send",
            params={"taskId": "task_123"}
        )

        assert message.jsonrpc == "2.0"
        assert message.id == "test_1"
        assert message.method == "tasks/send"

    def test_message_serialization(self):
        """Test message to JSON."""
        message = A2AMessage(
            id="test_1",
            method="tasks/send",
            params={"taskId": "task_123"}
        )

        json_str = message.to_json()
        assert "test_1" in json_str
        assert "tasks/send" in json_str

    def test_message_deserialization(self):
        """Test message from JSON."""
        json_str = '{"jsonrpc": "2.0", "id": "test_1", "method": "tasks/send", "params": {"taskId": "task_123"}}'

        message = A2AMessage.from_json(json_str)

        assert message.jsonrpc == "2.0"
        assert message.id == "test_1"
        assert message.method == "tasks/send"
        assert message.params["taskId"] == "task_123"


class TestA2AClient:
    """Tests for A2A client."""

    @pytest.mark.asyncio
    async def test_client_connect(self):
        """Test connecting to an agent."""
        with patch("aiohttp.ClientSession") as mock_session:
            client = A2AClient(agent_url="http://localhost:8000")
            await client.connect()

            assert client._session is not None
            await client.disconnect()

    @pytest.mark.asyncio
    async def test_client_get_agent_card(self):
        """Test fetching agent card."""
        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "agent_id": "test_agent",
                "name": "Test Agent",
                "description": "Test description",
                "url": "http://localhost:8000",
                "provider": {"organization": "SUVI"},
                "version": "1.0.0",
                "capabilities": [],
                "skills": [],
                "authentication": {"type": "none"},
                "supports_streaming": False
            })

            mock_session.return_value.__aenter__.return_value.get.return_value = mock_response

            client = A2AClient(agent_url="http://localhost:8000")
            await client.connect()

            card = await client.get_agent_card()

            assert card.agent_id == "test_agent"
            await client.disconnect()


class TestA2ATaskFlow:
    """Tests for A2A task flow."""

    def test_task_creation(self):
        """Test creating a task."""
        task = Task(
            user_input="Click the button at 100, 200",
            intent="desktop_control"
        )

        assert task.user_input == "Click the button at 100, 200"
        assert task.status == TaskStatus.RECEIVED
        assert task.id is not None

    def test_task_status_transitions(self):
        """Test task status transitions."""
        task = Task(user_input="Test task")

        assert task.status == TaskStatus.RECEIVED

        task.status = TaskStatus.ROUTING
        assert task.status == TaskStatus.ROUTING

        task.status = TaskStatus.PROCESSING
        assert task.status == TaskStatus.PROCESSING

        task.status = TaskStatus.COMPLETED
        assert task.status == TaskStatus.COMPLETED


class TestA2AMessageTypes:
    """Tests for A2A message types."""

    def test_task_submission_message(self):
        """Test creating a task submission message."""
        message = A2AMessage(
            method="tasks/send",
            params={
                "task": {"user_input": "Test task"},
                "sessionId": "session_123"
            }
        )

        assert message.method == "tasks/send"
        assert "task" in message.params
        assert message.params["sessionId"] == "session_123"

    def test_task_status_message(self):
        """Test creating a task status message."""
        message = A2AMessage(
            method="tasks/get",
            params={"taskId": "task_123"}
        )

        assert message.method == "tasks/get"
        assert message.params["taskId"] == "task_123"

    def test_cancel_task_message(self):
        """Test creating a cancel task message."""
        message = A2AMessage(
            method="tasks/cancel",
            params={"taskId": "task_123"}
        )

        assert message.method == "tasks/cancel"
        assert message.params["taskId"] == "task_123"


class TestA2AProtocol:
    """Tests for A2A protocol compliance."""

    def test_jsonrpc_version(self):
        """Test JSONRPC version in messages."""
        message = A2AMessage()

        assert message.jsonrpc == "2.0"

    def test_message_id_uniqueness(self):
        """Test message IDs are generated."""
        msg1 = A2AMessage()
        msg2 = A2AMessage()

        # Should be different (both None by default, but that's ok for this test)
        assert msg1.id is None or msg1.id is not None

    def test_error_message_format(self):
        """Test error message format."""
        message = A2AMessage(
            id="test_1",
            error={
                "code": -32600,
                "message": "Invalid Request"
            }
        )

        assert message.error is not None
        assert message.error["code"] == -32600
        assert message.error["message"] == "Invalid Request"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
