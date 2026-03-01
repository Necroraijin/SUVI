from agents.orchestrator.system_prompt import ORCHESTRATOR_PROMPT

class PromptComposer:
    """Assembles the final context window for the Orchestrator LLM."""
    
    @staticmethod
    def build_payload(user_input: str, memory_context: str, system_state: dict) -> str:
        """Combines all context streams into a single prompt for Gemini."""
        
        # Format the current OS state (e.g., what app is currently open)
        state_str = "\n".join([f"- {k}: {v}" for k, v in system_state.items()])
        
        payload = f"""
{ORCHESTRATOR_PROMPT}

# CURRENT SYSTEM STATE
{state_str if state_str else "No active window data."}

# RETRIEVED MEMORY CONTEXT
{memory_context if memory_context else "No relevant past memory found."}

# USER COMMAND
{user_input}
"""
        return payload.strip()