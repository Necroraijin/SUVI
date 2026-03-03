def generate_new_code(prompt: str, language: str = "python") -> dict:
    """
    Tool to command the LLM to generate code from scratch based on a description.
    """
    print(f"[Tool: generate_code] Writing new {language} code for: {prompt}")
    
    # In a full Vertex deployment, the agent uses its generative capabilities directly.
    # This tool format tells the desktop to wait for the LLM output and write it.
    mock_code = f"# Generated {language} script for: {prompt}\n\ndef main():\n    pass\n"
    
    return {
        "action": "write_file",
        "args": {"file_path": "generated_script.py", "content": mock_code}
    }