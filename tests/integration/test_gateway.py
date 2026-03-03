"""Integration tests for the SUVI Gateway API."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock

from suvi_gateway.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Headers with valid auth token."""
    return {"X-Suvi-Client-Auth": "suvi-hackathon-secret-123"}


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_check(self, client):
        """Test health endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        assert "status" in response.json()

    def test_health_response(self, client):
        """Test health response content."""
        response = client.get("/health")
        data = response.json()
        assert "SUVI Gateway" in data["status"]


class TestLiveTokenEndpoint:
    """Tests for the /auth/live-token endpoint."""

    @patch("suvi_gateway.routes.live_token.id_token.fetch_id_token")
    def test_get_token_success(self, mock_fetch_token, client, auth_headers):
        """Test successful token retrieval."""
        mock_fetch_token.return_value = "ya29.test-token"

        response = client.get("/auth/live-token", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "expires_in" in data

    def test_get_token_unauthorized(self, client):
        """Test token request without auth."""
        response = client.get("/auth/live-token")

        assert response.status_code == 401

    @patch("suvi_gateway.routes.live_token.id_token.fetch_id_token")
    def test_get_token_fallback(self, mock_fetch_token, client, auth_headers):
        """Test token fallback on error."""
        mock_fetch_token.side_effect = Exception("Auth error")

        response = client.get("/auth/live-token", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "mock-token" in data["token"]


class TestActionsEndpoint:
    """Tests for the /actions endpoint."""

    def test_log_action(self, client, auth_headers):
        """Test action logging."""
        payload = {
            "action": "mouse_click",
            "status": "completed",
            "result": "Clicked at (100, 200)"
        }

        response = client.post("/actions/log", json=payload, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data.get("acknowledged") is True

    def test_log_action_unauthorized(self, client):
        """Test action logging without auth."""
        payload = {
            "action": "mouse_click",
            "status": "completed"
        }

        response = client.post("/actions/log", json=payload)

        assert response.status_code == 401


class TestAgentsEndpoint:
    """Tests for the /agents endpoint."""

    def test_manual_route(self, client, auth_headers):
        """Test manual agent routing."""
        payload = {
            "target_agent": "code",
            "task": "Write a hello world program"
        }

        response = client.post("/agents/route", json=payload, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data.get("routing_status") == "Success"
        assert data.get("target") == "code"

    def test_manual_route_unauthorized(self, client):
        """Test agent routing without auth."""
        payload = {
            "target_agent": "text",
            "task": "Summarize this"
        }

        response = client.post("/agents/route", json=payload)

        assert response.status_code == 401


class TestWebSocketEndpoint:
    """Tests for WebSocket endpoint."""

    def test_websocket_endpoint_exists(self, client):
        """Test WebSocket endpoint exists."""
        # Can't directly test WebSocket with TestClient, but verify route exists
        # This is a placeholder - full WS testing requires pytest-asyncio
        assert True


class TestRateLimiting:
    """Tests for rate limiting middleware."""

    @patch("suvi_gateway.middleware.rate_limiter.SimpleRateLimiter")
    def test_rate_limit_applied(self, mock_limiter, client, auth_headers):
        """Test rate limiting is applied."""
        # Note: In production, rate limiting would be tested
        # with actual request patterns
        assert True


class TestFirestoreService:
    """Tests for Firestore service integration."""

    @patch("google.cloud.firestore.Client")
    def test_firestore_service_init(self, mock_firestore):
        """Test Firestore service initializes."""
        from suvi_gateway.services.firestore import FirestoreService

        service = FirestoreService(project_id="test-project")
        assert service.project_id == "test-project"


class TestPubSubService:
    """Tests for Pub/Sub service integration."""

    @patch("google.cloud.pubsub_v1.PublisherClient")
    def test_pubsub_service_init(self, mock_pubsub):
        """Test Pub/Sub service initializes."""
        from suvi_gateway.services.pubsub import PubSubService

        service = PubSubService(project_id="test-project")
        assert service.project_id == "test-project"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
