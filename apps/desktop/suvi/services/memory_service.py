import os
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from datetime import datetime
from typing import Any, Dict

class MemoryService:
    """
    Manages long-term memory and user persona data.
    Gracefully falls back to local memory if GCP/Firestore is unavailable.
    """
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID", "suvi-hackathon-2025")
        self.db = None
        self.local_persona_cache = {}
        
        try:
            
            if os.getenv("MOCK_AUTH") != "true":
                self.db = firestore.AsyncClient(project=self.project_id)
                print(f"📡 Firestore initialized for project: {self.project_id}")
        except Exception as e:
            print(f"⚠️ Firestore Init Warning: {e}. Using local memory fallback.")

    async def get_user_persona(self, user_id: str) -> Dict[str, Any]:
        """Fetches user preferences and persona."""
        if not self.db or user_id == "dev_user_001":
            return self.local_persona_cache.get(user_id, {})

        try:
            doc_ref = self.db.collection("users").document(user_id)
            doc = await doc_ref.get()
            if doc.exists:
                return doc.to_dict()
        except Exception as e:
            print(f"⚠️ Memory fetch failed: {e}. Falling back to local.")
        
        return self.local_persona_cache.get(user_id, {})

    async def save_user_persona(self, user_id: str, data: Dict[str, Any]):
        """Saves user preferences."""
        self.local_persona_cache[user_id] = data
        if not self.db:
            return

        try:
            doc_ref = self.db.collection("users").document(user_id)
            await doc_ref.set(data, merge=True)
        except Exception as e:
            print(f"⚠️ Memory save failed: {e}")

    async def get_recent_memory(self, user_id: str, limit: int = 5) -> list:
        """Fetches the recent tasks performed by the user to provide context."""
        recent_tasks = []
        if not self.db:
            return recent_tasks
            
        try:
            query = self.db.collection("suvi_memory") \
                           .where(filter=FieldFilter("user_id", "==", user_id)) \
                           .order_by("timestamp", direction=firestore.Query.DESCENDING) \
                           .limit(limit)
            
            docs = await query.get()
            for doc in docs:
                data = doc.to_dict()
                recent_tasks.append(f"Intent: {data.get('intent')} (Status: {data.get('status')})")
        except Exception as e:
            print(f"⚠️ Failed to fetch recent memory: {e}")
            
        return recent_tasks

    async def log_task_execution(self, user_id: str, session_id: str, intent: str, actions: list, status: str):
        """Logs a completed task for future recall."""
        print(f"📝 Logging task to memory: {intent} ({status})")
        if not self.db:
            return

        try:
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
        except Exception as e:
            print(f"⚠️ Task logging failed: {e}")
