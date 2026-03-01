def generate_new_code(prompt: str, language: str = "python") -> str:
    """
    Tool for the Code Agent to generate brand new scripts or classes from scratch.
    """
    print(f"[Tool: generate_code] Writing {language} code for: {prompt}")
    
    # In full deployment, the agent relies on its native LLM generation for this,
    # but having it as an explicit tool helps the Orchestrator track the action.
    return f"# Generated {language} code for: {prompt}\n\ndef generated_function():\n    pass\n"