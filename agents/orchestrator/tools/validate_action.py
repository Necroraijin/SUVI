from agents.orchestrator.validator import OutputValidator
from agents.shared.models import AgentResponse

def validate_sub_agent_output(status: str, result_text: str) -> bool:
    """
    Tool for the Orchestrator to run quality control on a sub-agent's output.
    
    Args:
        status: The status returned by the sub-agent (e.g., "success", "failed").
        result_text: The actual data or code returned by the sub-agent.
        
    Returns:
        True if the output is safe and accurate, False if it needs to be redone.
    """
    validator = OutputValidator()
    print("[Tool: validate_action] Orchestrator is checking sub-agent output quality.")
    
    mock_response = AgentResponse(status=status, result=result_text)
    return validator.validate(mock_response)