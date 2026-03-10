import os
from google.cloud import firestore
from datetime import datetime

class FirestoreService:
    """
    Production Firestore service. 
    Forces explicit project usage to avoid multi-account collision.
    """
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID", "project-0d0747b3-f100-478f-9b6")
        # Explicitly pass the project to ensure we don't default to the 'Primary' account's project
        try:
            self.db = firestore.AsyncClient(project=self.project_id)
            print(f"🔥 Firestore Service initialized for project: {self.project_id}")
        except Exception as e:
            print(f"❌ Failed to initialize Firestore: {e}")
            self.db = None

    async def log_session_start(self, session_id: str, user_id: str):
        if not self.db: return
        doc_ref = self.db.collection("sessions").document(session_id)
        await doc_ref.set({
            "user_id": user_id,
            "started_at": datetime.utcnow(),
            "status": "active"
        })

    async def save_message(self, session_id: str, role: str, text: str):
        if not self.db: return
        doc_ref = self.db.collection("sessions").document(session_id).collection("messages").document()
        await doc_ref.set({
            "role": role,
            "text": text,
            "timestamp": datetime.utcnow()
        })

    async def log_action(self, session_id: str, action_data: dict):
        if not self.db: return
        doc_ref = self.db.collection("sessions").document(session_id).collection("actions").document()
        await doc_ref.set({
            **action_data,
            "timestamp": datetime.utcnow()
        })
