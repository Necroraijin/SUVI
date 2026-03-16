
from google.genai import types

# -----------------------------------------------------------
# TOOL SCHEMA
# -----------------------------------------------------------

def get_function_declarations():
    """
    Tools available to the Gemini Live voice model.


    The Live model cannot control the computer directly,
    so it must call these tools which SUVI routes to the
    appropriate backend agents.
    """
    return [

        types.FunctionDeclaration(
            name="execute_computer_task",
            description="""


    Execute a task on the user's desktop computer.

    Examples:

    * open chrome
    * search cats on youtube
    * open notepad and type hello
    * scroll the page
    * click the first result
      """,
      parameters=types.Schema(
      type=types.Type.OBJECT,
      properties={
      "intent": types.Schema(
      type=types.Type.STRING,
      description="The full natural language instruction describing the desktop task."
      )
      },
      required=["intent"],
      ),
      ),

      
        types.FunctionDeclaration(
            name="coder_agent",
            description="""
      

    Use this when the user asks for programming help.

    Examples:

    * write python quicksort
    * fix this javascript error
    * explain this code
      """,
      parameters=types.Schema(
      type=types.Type.OBJECT,
      properties={
      "prompt": types.Schema(
      type=types.Type.STRING,
      description="The coding request."
      ),
      "language": types.Schema(
      type=types.Type.STRING,
      description="Optional programming language."
      ),
      },
      required=["prompt"],
      ),
      ),

      
        types.FunctionDeclaration(
            name="research_agent",
            description="""
      

    Use this when the user asks factual questions or research queries.

    Examples:

    * what is quantum computing
    * latest AI news
    * explain black holes
      """,
      parameters=types.Schema(
      type=types.Type.OBJECT,
      properties={
      "query": types.Schema(
      type=types.Type.STRING,
      description="The research query."
      )
      },
      required=["query"],
      ),
      ),

      
        types.FunctionDeclaration(
            name="describe_screen",
            description="""
      

    Describe the current desktop screen for accessibility.

    Use when user asks:

    * what is on my screen
    * can you see this
    * describe the screen
      """
      ),

      
        types.FunctionDeclaration(
            name="stop_execution",
            description="""
      

    Stop the currently running automation task.

    Triggered when the user says:

    * stop
    * cancel
    * abort
      """
      ),

      ]

# -----------------------------------------------------------
# TRIGGER PARSER
# -----------------------------------------------------------
def extract_computer_task(text: str) -> str | None: 
    """
    Extracts the command from the trigger format.
    
    
    Example input:
    "[CALL_TOOL: execute_computer_task] open chrome"
    
    Returns:
    "open chrome"
    """
    
    if not text:
        return None
    
    trigger = "[CALL_TOOL: execute_computer_task]"
    
    if trigger not in text:
        return None
    
    return text.split(trigger, 1)[1].strip()

# -----------------------------------------------------------
# HELPER DETECTORS
# -----------------------------------------------------------

def is_stop_command(text: str) -> bool:
    """Checks if the text contains a stop command."""
    
    text = text.lower()
    
    stop_words = [
        "stop",
        "cancel",
        "abort",
        "wait",
        "pause"
    ]
    
    return any(word in text for word in stop_words)
