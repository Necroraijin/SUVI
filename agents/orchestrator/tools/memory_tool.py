from google.cloud import firestore
import os

class MemoryTool:
    def __init__(self):
        self.db = firestore.AsyncClient(project=os.getenv("GCP_PROJECT_ID"))

    async def search(self, query: str, user_id: str) -> str:
        """Search memory for relevant context."""
        try:
            docs = self.db.collection("sessions").where("user_id", "==", user_id).order_by("started_at", direction=firestore.Query.DESCENDING).limit(5).stream()
            context = []
            async for doc in docs:
                context.append(str(doc.to_dict()))
            return "\n".join(context) if context else "No past context found."
        except Exception as e:
            return f"Error searching memory: {e}"

memory_tool = MemoryTool()
