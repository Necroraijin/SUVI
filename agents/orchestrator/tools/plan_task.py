from agents.orchestrator.planner import TaskPlanner

def plan_multi_step_task(user_intent: str) -> list[dict]:
    """
    Tool for the Orchestrator to break down a complex request into a sequence of sub-agent tasks.
    
    Args:
        user_intent: The complex instruction from the user (e.g., "Research AI startups and save to a file").
        
    Returns:
        A list of dictionaries representing the step-by-step execution plan.
    """
    planner = TaskPlanner()
    print(f"[Tool: plan_task] Orchestrator is generating a plan for: {user_intent}")
    return planner.create_plan(user_intent)