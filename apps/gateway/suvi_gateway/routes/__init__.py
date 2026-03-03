"""SUVI Gateway Routes - API endpoints for the gateway service."""

from suvi_gateway.routes import health, live_token, actions, agents

__all__ = ["health", "live_token", "actions", "agents"]
