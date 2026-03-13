You are helping refactor a Python desktop AI assistant called **SUVI** that uses the Gemini Live API, a tool-calling agent loop, and desktop automation.

The current system works but has several architectural issues that must be fixed. Refactor the code to solve all of the following problems.

---

PROJECT GOAL

SUVI is a desktop AI assistant that:

* Uses Gemini Live API for voice interaction
* Uses a reasoning agent loop to decide actions
* Executes actions using a dispatcher and desktop automation tools
* Stores memory in Firestore
* Saves replays to Google Cloud Storage
* Uses wake word detection

---

PROBLEMS TO FIX

1. The model produces extremely long explanations instead of tool calls.

Example output currently looks like this:

"Opening Google Chrome on a desktop can be done in several ways… Method 1… Method 2…"

This wastes tokens and slows the agent.

Fix:
Rewrite the system prompt so the model ONLY returns tool calls.

System prompt rules must include:

* Do NOT explain actions
* Do NOT output step-by-step instructions
* Only call tools
* Be concise

Example desired output:

{
"function_call": {
"name": "launch_application",
"args": {"app_name": "chrome"}
}
}

---

1. The current tools are poorly defined.

Current tools:

open_web_browser
click_at
type_text_at

These are ambiguous and cause incorrect behavior (example: Win+D was triggered instead of launching Chrome).

Refactor tools to deterministic atomic tools:

launch_application(app_name)
open_url(url)
click_at(x, y)
type_text(text)
press_key(key)
wait(seconds)

Example correct tool usage:

launch_application("chrome")
open_url("<https://google.com>")
type_text("iphone 17 pro max")
press_key("enter")

Also update the dispatcher to handle these new tools.

---

1. Fix the function calling protocol.

Currently errors appear:

"Each Function Response must be matched to a Function Call by name."

Ensure the agent loop correctly returns:

function_call → dispatcher executes → function_response returned with the SAME name.

Example:

Model call:

{
"function_call": {
"name": "launch_application",
"args": {"app_name": "chrome"}
}
}

Dispatcher returns:

{
"function_response": {
"name": "launch_application",
"response": "success"
}
}

---

1. Fix Gemini Live send loop errors.

Current error:

Unsupported input type "google.genai.types.Content"

Fix by ensuring the websocket session sends either:

session.send("text")

OR

session.send({
"role": "user",
"parts": [{"text": "message"}]
})

Do not send Content objects directly.

---

1. Prevent excessive reconnections to Gemini Live.

Current logs show the system reconnecting repeatedly:

[Live] Connecting to Gemini...

Fix:

Maintain a single websocket session during interaction.

Correct lifecycle:

wake word detected
open websocket session
process conversation and actions
close session when finished

---

1. Optimize agent reasoning.

Currently every step uses a new model call.

Refactor so the agent produces a small plan in a single reasoning step.

Example plan:

[
{"tool": "launch_application", "args": {"app_name": "chrome"}},
{"tool": "open_url", "args": {"url": "https://google.com"}},
{"tool": "type_text", "args": {"text": "iphone 17 pro max"}},
{"tool": "press_key", "args": {"key": "enter"}}
]

Then execute sequentially.

---

1. Ensure Chrome launches reliably.

Implement launch_application using subprocess instead of UI automation.

Example:

Windows:
subprocess.Popen("chrome")

Mac:
subprocess.Popen(["open", "-a", "Google Chrome"])

Linux:
subprocess.Popen(["google-chrome"])

---

FINAL TASK

Refactor the SUVI codebase to implement all fixes above while keeping existing components:

* Wake word detection
* Gemini Live audio streaming
* Firestore memory
* Replay recording
* GCS uploads

Produce clean, modular Python code for:

* agent loop
* tool definitions
* dispatcher
* Gemini Live session manager
* improved system prompt

The final system should:

1. Produce concise tool calls
2. Execute deterministic desktop actions
3. Avoid unnecessary API calls
4. Maintain stable Gemini Live sessions
5. Eliminate the current errors.
