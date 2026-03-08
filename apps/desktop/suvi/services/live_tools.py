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
                        description="A detailed, actionable description of what needs to be done on the screen. E.g. 'Click the Start button', 'Open Chrome and go to youtube.com', 'Read the email from John'."
                    )
                },
                required=["intent"]
            )
        ),
        types.FunctionDeclaration(
            name="stop_execution",
            description="Immediately halts any ongoing computer task. Call this if the user says 'stop', 'cancel', or 'wait'.",
        )
    ]
