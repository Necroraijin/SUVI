import os
from google.cloud import firestore
from datetime import datetime
from typing import Any, Dict, Optional

class MemoryService:
    """
    Manages long-term memory and user persona data via Google Cloud Firestore.
    Ensures SUVI remembers preferences, personal facts, and past actions.
    """
    def __init__(self, project_id: Optional[str] = None):
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID")
        if self.project_id:
            self.db = firestore.AsyncClient(project=self.project_id)
        else:
            print("⚠️ GCP_PROJECT_ID not set. MemoryService running in mock mode.")
            self.db = None

    async def save_user_fact(self, user_id: str, fact_key: str, value: Any):
        """Stores a personal fact or preference (e.g., 'likes_dark_mode': True)."""
        if not self.db: return
        doc_ref = self.db.collection("users").document(user_id).collection("persona").document(fact_key)
        await doc_ref.set({
            "value": value,
            "timestamp": datetime.utcnow()
        })
        print(f"💾 Personal fact saved: {fact_key} = {value}")

    async def get_user_persona(self, user_id: str) -> Dict[str, Any]:
        """Retrieves the full persona context for a user."""
        if not self.db: return {}
        persona = {}
        docs = self.db.collection("users").document(user_id).collection("persona").stream()
        async for doc in docs:
            persona[doc.id] = doc.to_dict().get("value")
        return persona

    async def log_task_execution(self, user_id: str, session_id: str, intent: str, actions: list, status: str):
        """Logs a completed desktop task for future audit and recall."""
        if not self.db: return
        doc_ref = self.db.collection("suvi_memory").document()
        await doc_ref.set({
            "user_id": user_id,
            "session_id": session_id,
            "timestamp": datetime.utcnow(),
            "intent": intent,
            "actions_taken": actions,
            "status": status,
            "type": "computer_use_task"
        })
        print(f"💾 Task memory logged to Firestore.")
