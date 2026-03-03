"""Memory Agent - Persistent context management and memory recall."""

import os
from typing import Optional, Any
from datetime import datetime

from google.cloud import firestore
from google.cloud import aiplatform

from agents.shared.agent_utils import GeminiAgent
from shared.suvi_types import AgentType, AgentCard, Task, AgentResult, AgentResultStatus
from shared.a2a import A2AServer


GCP_PROJECT = os.environ.get("GCP_PROJECT", "suvi-project")


class MemoryAgent(GeminiAgent, A2AServer):
    """Agent for managing persistent user memory across tiers."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8006):
        GeminiAgent.__init__(self,
            agent_type=AgentType.MEMORY,
            system_prompt="""You are SUVI Memory Agent, managing persistent user context.

Memory Tiers:
- Hot (0ms): Current conversation context in Gemini Live
- Warm (<20ms): Firestore document cache for current day
- Cold (<100ms): Vertex AI Vector Search for semantic recall

You store and recall relevant information from user's history.
Always maintain context across conversations.
Prioritize recent memories over older ones.""",
            model_override="gemini-2.0-flash-001"
        )
        
        card = AgentCard(
            agent_id="suvi-memory-agent",
            name="MemoryAgent",
            description="Persistent context management and memory recall agent.",
            url=f"http://{host}:{port}",
            provider={"name": "SUVI"},
            capabilities=[]
        )
        A2AServer.__init__(self, agent_card=card, host=host, port=port)

        # Initialize Firestore
        self.db = firestore.Client(project=GCP_PROJECT)

        # Initialize Vector Search index for cold memory
        try:
            aiplatform.init(project=GCP_PROJECT, location="us-central1")
        except Exception as e:
            print(f"[MemoryAgent] Vector Search init warning: {e}")

    async def execute_task(self, task: Task) -> Optional[AgentResult]:
        """A2A Protocol entry point for executing a task."""
        try:
            output = await self.process_task(task.user_input)
            
            return AgentResult(
                agent_type=AgentType.MEMORY,
                task_id=task.id,
                status=AgentResultStatus.SUCCESS,
                output=output
            )
        except Exception as e:
            return AgentResult(
                agent_type=AgentType.MEMORY,
                task_id=task.id,
                status=AgentResultStatus.ERROR,
                error=str(e)
            )

    async def store_memory(
        self,
        user_id: str,
        content: str,
        memory_type: str = "conversation",
        importance: int = 5
    ) -> str:
        """Store a memory in Firestore (warm tier)."""
        doc_ref = self.db.collection("users").document(user_id).collection("memories").document()

        memory_data = {
            "content": content,
            "type": memory_type,
            "importance": importance,
            "timestamp": datetime.now(),
            "embedding": None  # Would generate embedding for vector search
        }

        doc_ref.set(memory_data)

        return f"Memory stored with ID: {doc_ref.id}"

    async def recall_memory(
        self,
        user_id: str,
        query: str,
        limit: int = 5
    ) -> str:
        """Recall relevant memories from all tiers."""
        # First check warm tier (Firestore)
        memories = []
        docs = (
            self.db.collection("users")
            .document(user_id)
            .collection("memories")
            .order_by("timestamp", direction=firestore.Query.DESCENDING)
            .limit(limit)
            .stream()
        )

        for doc in docs:
            data = doc.to_dict()
            memories.append({
                "id": doc.id,
                "content": data.get("content", ""),
                "timestamp": data.get("timestamp"),
                "type": data.get("type", "conversation")
            })

        if memories:
            memory_text = "\n".join([f"- {m['content']}" for m in memories])
            prompt = f"""Based on the user's memory history:

{memory_text}

Answer the following query:
{query}

If relevant memories exist, incorporate them into your response.
If no relevant memories exist, indicate that."""
            return await self.generate(prompt)

        return "No relevant memories found."

    async def get_session_context(self, user_id: str) -> dict:
        """Get current session context (hot tier)."""
        # Get today's session data from Firestore
        today = datetime.now().strftime("%Y-%m-%d")
        docs = (
            self.db.collection("users")
            .document(user_id)
            .collection("sessions")
            .document(today)
            .collection("messages")
            .order_by("timestamp")
            .limit(20)
            .stream()
        )

        messages = []
        for doc in docs:
            data = doc.to_dict()
            messages.append({
                "role": data.get("role", "user"),
                "content": data.get("content", ""),
                "timestamp": str(data.get("timestamp", ""))
            })

        return {
            "date": today,
            "messages": messages,
            "message_count": len(messages)
        }

    async def process_task(self, task: str, operation: str = "recall", **kwargs) -> str:
        """Process memory task using Gemini Tool Binding."""
        # For memory agent, we need to inject the user_id context into the prompt
        user_id = kwargs.get("user_id", "default_user")
        
        tools = [
            self.store_memory,
            self.recall_memory,
            self.get_session_context
        ]
        
        prompt = f"User ID: {user_id}\nUser Request: {task}"
        return await self.generate(prompt, tools=tools)
