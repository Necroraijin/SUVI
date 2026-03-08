import asyncio
from google.genai import types

def get_function_declarations():
    """
    Returns the tool definitions that we expose to the Live Audio session.
    The Live Audio model cannot click/type on its own, but it can CALL these functions
    which we will then intercept and pass to the Computer Use Vertex AI model.
    """
    return [
        types.FunctionDeclaration(
            name="execute_computer_task",
            description="Executes a visual UI task on the user's computer (clicking, typing, scrolling, finding information on screen). Call this when the user asks you to interact with their desktop, open apps, click things, or read their screen.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "intent": types.Schema(
                        type=types.Type.STRING,
                        description="A detailed, actionable description of what needs to be done on the screen."
                    )
                },
                required=["intent"]
            )
        ),
        types.FunctionDeclaration(
            name="coder_agent",
            description="Invokes a specialized coding agent for writing, debugging, or explaining code. Use this when the user has complex programming questions or needs code generated.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "prompt": types.Schema(
                        type=types.Type.STRING,
                        description="The coding task or question."
                    ),
                    "language": types.Schema(
                        type=types.Type.STRING,
                        description="The programming language (e.g., python, javascript)."
                    )
                },
                required=["prompt"]
            )
        ),
        types.FunctionDeclaration(
            name="research_agent",
            description="Invokes a research agent to search the web and synthesize information. Use this for facts, news, or complex information gathering that isn't on the user's screen.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "query": types.Schema(
                        type=types.Type.STRING,
                        description="The search query or research topic."
                    )
                },
                required=["query"]
            )
        ),
        types.FunctionDeclaration(
            name="describe_screen",
            description="Captures the user's screen and provides a detailed verbal description of what is visible. Use this when the user asks 'what's on my screen?', 'can you see this?', or if they are visually impaired and need navigation help.",
        ),
        types.FunctionDeclaration(
            name="stop_execution",
            description="Immediately halts any ongoing computer task. Call this if the user says 'stop', 'cancel', or 'wait'.",
        )
    ]
