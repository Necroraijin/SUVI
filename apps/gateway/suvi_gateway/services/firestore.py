"""Google Cloud Firestore service for persistent storage."""

import os
from typing import Optional, Any
from datetime import datetime
from google.cloud import firestore


class FirestoreService:
    """Firestore service for persistent memory and user data."""

    def __init__(self, project_id: str = None):
        self.project_id = project_id or os.environ.get("GCP_PROJECT", "suvi-project")
        self.db = firestore.Client(project=self.project_id)

    def get_user_profile(self, user_id: str) -> Optional[dict]:
        """
        Get user profile from Firestore.

        Args:
            user_id: The user ID

        Returns:
            User profile dict or None
        """
        try:
            doc_ref = self.db.collection("users").document(user_id)
            doc = doc_ref.get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"[Firestore] Error fetching user profile: {e}")
            return None

    def save_user_profile(self, user_id: str, profile: dict) -> bool:
        """Save user profile to Firestore."""
        try:
            doc_ref = self.db.collection("users").document(user_id)
            doc_ref.set(profile, merge=True)
            return True
        except Exception as e:
            print(f"[Firestore] Error saving user profile: {e}")
            return False

    def save_memory(self, user_id: str, memory: dict) -> str:
        """Save a memory to Firestore."""
        try:
            doc_ref = (
                self.db.collection("users")
                .document(user_id)
                .collection("memories")
                .document()
            )
            memory["timestamp"] = datetime.now()
            doc_ref.set(memory)
            return doc_ref.id
        except Exception as e:
            print(f"[Firestore] Error saving memory: {e}")
            return ""

    def get_memories(
        self,
        user_id: str,
        limit: int = 10,
        memory_type: Optional[str] = None
    ) -> list[dict]:
        """Get memories from Firestore."""
        try:
            collection_ref = (
                self.db.collection("users")
                .document(user_id)
                .collection("memories")
            )

            query = collection_ref.order_by(
                "timestamp", direction=firestore.Query.DESCENDING
            ).limit(limit)

            if memory_type:
                query = query.where("type", "==", memory_type)

            docs = query.stream()
            return [doc.to_dict() for doc in docs]

        except Exception as e:
            print(f"[Firestore] Error getting memories: {e}")
            return []

    def save_session_data(self, user_id: str, session_id: str, data: dict) -> bool:
        """Save session data."""
        try:
            doc_ref = (
                self.db.collection("users")
                .document(user_id)
                .collection("sessions")
                .document(session_id)
            )
            data["updated_at"] = datetime.now()
            doc_ref.set(data, merge=True)
            return True
        except Exception as e:
            print(f"[Firestore] Error saving session data: {e}")
            return False

    def get_session_data(self, user_id: str, session_id: str) -> Optional[dict]:
        """Get session data."""
        try:
            doc_ref = (
                self.db.collection("users")
                .document(user_id)
                .collection("sessions")
                .document(session_id)
            )
            doc = doc_ref.get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"[Firestore] Error getting session data: {e}")
            return None

    def log_action(self, user_id: str, action: dict) -> str:
        """Log an action to Firestore."""
        try:
            doc_ref = (
                self.db.collection("users")
                .document(user_id)
                .collection("actions")
                .document()
            )
            action["timestamp"] = datetime.now()
            action["user_id"] = user_id
            doc_ref.set(action)
            return doc_ref.id
        except Exception as e:
            print(f"[Firestore] Error logging action: {e}")
            return ""

    def get_action_history(
        self,
        user_id: str,
        limit: int = 50,
        action_type: Optional[str] = None
    ) -> list[dict]:
        """Get action history."""
        try:
            collection_ref = (
                self.db.collection("users")
                .document(user_id)
                .collection("actions")
            )

            query = collection_ref.order_by(
                "timestamp", direction=firestore.Query.DESCENDING
            ).limit(limit)

            if action_type:
                query = query.where("action_type", "==", action_type)

            docs = query.stream()
            return [doc.to_dict() for doc in docs]

        except Exception as e:
            print(f"[Firestore] Error getting action history: {e}")
            return []
