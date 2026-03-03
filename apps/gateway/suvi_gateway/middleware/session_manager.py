"""Session management for active desktop client connections."""

import uuid
import time
from typing import Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Session:
    """Represents an active client session."""
    session_id: str
    client_id: str
    user_id: str
    active_agent: str = "orchestrator"
    ring_state: str = "idle"
    history: list[dict] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)


class SessionManager:
    """Manages active client sessions and their state."""

    def __init__(self, session_timeout: int = 3600):
        """
        Initialize session manager.

        Args:
            session_timeout: Session timeout in seconds (default: 1 hour)
        """
        self._sessions: dict[str, Session] = {}
        self._client_sessions: dict[str, str] = {}  # client_id -> session_id
        self.session_timeout = session_timeout

    def create_session(
        self,
        client_id: str,
        user_id: str = "default_user",
        metadata: Optional[dict] = None
    ) -> Session:
        """
        Create a new session.

        Args:
            client_id: The client identifier
            user_id: The user identifier
            metadata: Optional session metadata

        Returns:
            The created Session
        """
        session_id = str(uuid.uuid4())

        session = Session(
            session_id=session_id,
            client_id=client_id,
            user_id=user_id,
            metadata=metadata or {}
        )

        self._sessions[session_id] = session
        self._client_sessions[client_id] = session_id

        print(f"[SessionManager] Created session {session_id} for client {client_id}")
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID."""
        session = self._sessions.get(session_id)

        if session and self._is_valid(session):
            return session

        return None

    def get_session_by_client(self, client_id: str) -> Optional[Session]:
        """Get session by client ID."""
        session_id = self._client_sessions.get(client_id)

        if session_id:
            return self.get_session(session_id)

        return None

    def update_session(
        self,
        session_id: str,
        active_agent: Optional[str] = None,
        ring_state: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> bool:
        """
        Update session state.

        Args:
            session_id: The session ID
            active_agent: New active agent
            ring_state: New ring state
            metadata: Metadata to merge

        Returns:
            True if updated successfully
        """
        session = self.get_session(session_id)

        if not session:
            return False

        if active_agent is not None:
            session.active_agent = active_agent

        if ring_state is not None:
            session.ring_state = ring_state

        if metadata:
            session.metadata.update(metadata)

        session.last_activity = time.time()
        return True

    def add_to_history(self, session_id: str, entry: dict) -> bool:
        """Add an entry to session history."""
        session = self.get_session(session_id)

        if not session:
            return False

        entry["timestamp"] = datetime.now().isoformat()
        session.history.append(entry)

        # Keep history manageable
        if len(session.history) > 100:
            session.history = session.history[-100:]

        session.last_activity = time.time()
        return True

    def end_session(self, session_id: str) -> bool:
        """End a session."""
        session = self._sessions.get(session_id)

        if not session:
            return False

        del self._sessions[session_id]

        if session.client_id in self._client_sessions:
            del self._client_sessions[session.client_id]

        print(f"[SessionManager] Ended session {session_id}")
        return True

    def end_session_by_client(self, client_id: str) -> bool:
        """End session by client ID."""
        session_id = self._client_sessions.get(client_id)

        if session_id:
            return self.end_session(session_id)

        return False

    def cleanup_stale_sessions(self) -> int:
        """Remove stale sessions that have timed out."""
        stale_sessions = []

        for session_id, session in self._sessions.items():
            if not self._is_valid(session):
                stale_sessions.append(session_id)

        for session_id in stale_sessions:
            self.end_session(session_id)

        if stale_sessions:
            print(f"[SessionManager] Cleaned up {len(stale_sessions)} stale sessions")

        return len(stale_sessions)

    def get_all_sessions(self) -> list[Session]:
        """Get all active sessions."""
        return [
            s for s in self._sessions.values()
            if self._is_valid(s)
        ]

    def _is_valid(self, session: Session) -> bool:
        """Check if session is still valid."""
        return (time.time() - session.last_activity) < self.session_timeout
