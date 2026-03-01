from agents.shared.memory_client import MemoryClient

def recall_user_context(query: str) -> str:
    """
    Tool for the Orchestrator to search the long-term memory database for user facts, 
    relationships, or past project context.
    
    Args:
        query: The specific subject to search for (e.g., "current projects", "favorite colors").
        
    Returns:
        A string containing the retrieved memory or a note that none was found.
    """
    memory = MemoryClient()
    print(f"[Tool: recall_memory] Orchestrator querying memory for: {query}")
    return memory.retrieve_context(query)