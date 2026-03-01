class TaskPlanner:
    """Deconstructs complex user prompts into sequential, multi-agent execution steps."""
    
    def __init__(self):
        self.active_plan = []

    def create_plan(self, user_intent: str) -> list[dict]:
        """
        In production, this would call Gemini to generate a JSON array of steps.
        For now, we build a simple sequential mock plan.
        """
        print(f"[Planner] Analyzing complex intent: '{user_intent}'")
        
        # Example hardcoded logic for multi-step tasks
        if "research" in user_intent.lower() and "save" in user_intent.lower():
            self.active_plan = [
                {"step": 1, "target": "Agent_Browser", "action": "Search and extract data"},
                {"step": 2, "target": "Agent_FileSystem", "action": "Write extracted data to file"}
            ]
        else:
            # Single step plan
            self.active_plan = [
                {"step": 1, "target": "Dynamic", "action": user_intent}
            ]
            
        print(f"[Planner] Generated {len(self.active_plan)}-step execution plan.")
        return self.active_plan