import os
from google.cloud import firestore
from datetime import datetime

class FirestoreService:
    def __init__(self):
        project_id = os.getenv("GCP_PROJECT_ID")
        self.db = firestore.AsyncClient(project=project_id)

    async def log_session_start(self, session_id: str, user_id: str):
        doc_ref = self.db.collection("sessions").document(session_id)
        await doc_ref.set({
            "user_id": user_id,
            "started_at": datetime.utcnow(),
            "status": "active"
        })

    async def save_message(self, session_id: str, role: str, text: str):
        doc_ref = self.db.collection("sessions").document(session_id).collection("messages").document()
        await doc_ref.set({
            "role": role,
            "text": text,
            "timestamp": datetime.utcnow()
        })

    async def log_action(self, session_id: str, action_data: dict):
        doc_ref = self.db.collection("sessions").document(session_id).collection("actions").document()
        await doc_ref.set({
            **action_data,
            "timestamp": datetime.utcnow()
        })
