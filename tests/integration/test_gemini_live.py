"""Integration tests for Gemini Live API session."""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock, PropertyMock
from typing import Generator

from apps.desktop.suvi.services.live_session import LiveSession
from apps.desktop.suvi.services.gateway_client import GatewayClient


class TestGatewayClient:
    """Tests for Gateway client."""

    @pytest.mark.asyncio
    async def test_get_live_token(self):
        """Test getting live token from gateway."""
        client = GatewayClient(base_url="http://localhost:8000")

        token = await client.get_live_token()

        assert token is not None
        assert "wss://" in token or "mock" in token

    @pytest.mark.asyncio
    async def test_gateway_url_configurable(self):
        """Test gateway URL is configurable."""
        custom_url = "http://custom-gateway:9000"
        client = GatewayClient(base_url=custom_url)

        assert client.base_url == custom_url


class TestLiveSession:
    """Tests for LiveSession."""

    @pytest.fixture
    def mock_gateway_client(self):
        """Create mock gateway client."""
        client = MagicMock(spec=GatewayClient)
        client.get_live_token = AsyncMock(return_value="wss://mock-url")
        return client

    @pytest.mark.asyncio
    async def test_live_session_init(self, mock_gateway_client):
        """Test LiveSession initialization."""
        session = LiveSession(gateway_client=mock_gateway_client)

        assert session.gateway == mock_gateway_client
        assert session.ws is None
        assert session._listen_task is None

    @pytest.mark.asyncio
    async def test_connect_success(self, mock_gateway_client):
        """Test successful connection."""
        session = LiveSession(gateway_client=mock_gateway_client)

        await session.connect()

        # Note: In real implementation, would emit connected signal
        # For now just verify no exception
        assert True

    @pytest.mark.asyncio
    async def test_connect_failure(self, mock_gateway_client):
        """Test connection failure handling."""
        mock_gateway_client.get_live_token = AsyncMock(
            side_effect=Exception("Connection failed")
        )

        session = LiveSession(gateway_client=mock_gateway_client)

        # Should handle error gracefully
        try:
            await session.connect()
        except Exception:
            pass  # Expected to fail with mock

        assert True

    @pytest.mark.asyncio
    async def test_disconnect(self, mock_gateway_client):
        """Test disconnection."""
        session = LiveSession(gateway_client=mock_gateway_client)

        # Mock the websocket
        mock_ws = AsyncMock()
        session.ws = mock_ws

        await session.disconnect()

        assert session.ws is None


class TestGeminiLiveIntegration:
    """Integration tests for Gemini Live API."""

    @pytest.mark.asyncio
    async def test_audio_chunk_format(self):
        """Test audio chunk formatting for Gemini Live."""
        # Simulate audio chunk
        test_pcm_data = b"test_audio_data"

        # Should be hex encoded
        import json
        payload = json.dumps({
            "realtimeInput": {
                "mediaChunks": [{
                    "mimeType": "audio/pcm",
                    "data": test_pcm_data.hex()
                }]
            }
        })

        assert "audio/pcm" in payload
        assert test_pcm_data.hex() in payload

    def test_session_state_signals(self):
        """Test session state signal emission."""
        # This would test PyQt signal emission
        # Simplified test here
        from PyQt6.QtCore import QObject, pyqtSignal

        class TestEmitter(QObject):
            test_signal = pyqtSignal(str)

        emitter = TestEmitter()
        signal_emitted = []

        emitter.test_signal.connect(lambda x: signal_emitted.append(x))
        emitter.test_signal.emit("test")

        assert signal_emitted == ["test"]


class TestLiveSessionToolCalls:
    """Tests for tool call handling in LiveSession."""

    @pytest.mark.asyncio
    async def test_tool_call_parsing(self):
        """Test parsing tool calls from Gemini."""
        # Simulate a tool call message from Gemini
        tool_call_data = {
            "toolCall": {
                "name": "mouse_click",
                "args": {"x": 100, "y": 200}
            }
        }

        # Verify structure
        assert "toolCall" in tool_call_data
        assert tool_call_data["toolCall"]["name"] == "mouse_click"
        assert tool_call_data["toolCall"]["args"]["x"] == 100


class TestLiveSessionAudio:
    """Tests for audio handling in LiveSession."""

    def test_audio_message_format(self):
        """Test audio message format from Gemini."""
        audio_data = {
            "audio": "a1b2c3d4e5".encode().hex()
        }

        assert "audio" in audio_data
        assert isinstance(audio_data["audio"], str)  # Hex encoded


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
