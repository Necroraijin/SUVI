from agents.orchestrator.router import TaskRouter

async def delegate_to_sub_agent(agent_name: str, task_description: str) -> dict:
    """
    Tool for the Orchestrator to hand off a specific, single-step task to a specialized sub-agent.
    
    Args:
        agent_name: The target agent (e.g., "Agent_Code", "Agent_Browser", "Agent_FileSystem").
        task_description: The exact instruction for the sub-agent.
        
    Returns:
        A dictionary containing the sub-agent's response status and result.
    """
    router = TaskRouter()
    print(f"[Tool: route_to_agent] Orchestrator delegating '{task_description}' to {agent_name}")
    
    # We pass the explicit target agent directly into the router's logic
    # In a full async environment, we await this call
    response = await router.route_request(task_description, context={"forced_target": agent_name})
    
    return {
        "status": response.status,
        "result": response.result
    }