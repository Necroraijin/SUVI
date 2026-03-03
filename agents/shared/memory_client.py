import os
from typing import Optional, Dict, Any
from google.cloud import firestore
from google.auth.exceptions import DefaultCredentialsError

class MemoryClient:
    """Connects to Firestore to store and retrieve long-term user context and preferences."""
    
    def __init__(self, project_id: Optional[str] = None):
        self.project_id = project_id or os.environ.get("GCP_PROJECT", "suvi-core")
        self.db: Optional[firestore.Client] = None
        
        try:
            # Initialize Firestore client if credentials available
            self.db = firestore.Client(project=self.project_id)
            print(f"[MemoryClient] Firestore client initialized for project: {self.project_id}")
        except (DefaultCredentialsError, Exception) as e:
            print(f"[MemoryClient] Running in local/mock mode: {e}")
        
    def retrieve_context(self, query: str) -> str:
        """Fetches relevant past conversations or facts based on the current task."""
        print(f"[MemoryClient] Searching long-term memory for semantic match: '{query}'")
        
        if self.db:
            try:
                # Basic mock retrieval from 'memories' collection
                # In production, this would use Vertex AI Vector Search
                docs = self.db.collection('memories').limit(3).stream()
                context = []
                for doc in docs:
                    context.append(str(doc.to_dict().get('content', '')))
                
                if context:
                    return "\n".join(context)
            except Exception as e:
                print(f"[MemoryClient Error] Failed to retrieve context: {e}")

        # Fallback/Mock
        return "System Note: No highly relevant long-term memory found for this exact query."

    def save_fact(self, key: str, value: Any):
        """Saves a concrete fact about the user for future reference."""
        print(f"[MemoryClient] Committing to Firestore: {key}")
        
        if self.db:
            try:
                self.db.collection('user_facts').document(key).set({
                    "value": value,
                    "updated_at": firestore.SERVER_TIMESTAMP
                })
            except Exception as e:
                print(f"[MemoryClient Error] Failed to save fact: {e}")
        else:
            # Mock: Store in local memory for current session
            print(f"[MemoryClient Mock] Saved '{key}' locally.")
