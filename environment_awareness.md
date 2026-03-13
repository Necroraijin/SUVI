Below is a **complete Markdown document** you can drop into your repo (for example: `docs/environment-awareness.md`).
It’s written so **Gemini CLI can read it and implement the feature**, and also so judges can understand the architecture if they browse your repo.

---

```markdown
# SUVI Environment Awareness System

## Overview

SUVI is an AI desktop agent designed to help users control their computer using natural language and voice.  
To make SUVI reliable and prevent hallucinations, it must understand the **actual environment of the user’s computer**.

Environment awareness allows SUVI to know:

- What applications are installed
- What programs are currently running
- What the default browser is
- What capabilities exist on the machine

This prevents the AI from attempting actions that are impossible on the user's system.

Example problem without environment awareness:

User command:
"Play a song on YouTube."

AI reasoning (incorrect):
Open YouTube application.

Actual computer state:
No YouTube application installed.

Correct reasoning:
Open browser → navigate to youtube.com → search song.

The Environment Awareness System solves this problem.

---

# Architecture

The system has four components.

1. Environment Scanner
2. Environment Index
3. Capability Mapper
4. AI Context Injection

Pipeline:

User installs SUVI  
↓  
Environment Scanner runs  
↓  
Environment Index created  
↓  
Capability map generated  
↓  
Context injected into Gemini orchestrator  
↓  
AI produces correct actions

---

# 1. Environment Scanner

The Environment Scanner runs when SUVI is first installed or launched.

Its job is to detect:

- Installed applications
- Default browser
- Operating system
- Running processes

The scanner then stores this information locally.

File location:

```

~/.suvi/environment.json

````

Example output:

```json
{
  "os": "Windows 11",
  "installed_apps": [
    "Google Chrome",
    "Microsoft Edge",
    "Spotify",
    "VLC"
  ],
  "default_browser": "Google Chrome",
  "music_players": ["Spotify"],
  "video_players": ["VLC"]
}
````

---

# Windows Implementation

The scanner can detect installed apps using the Windows registry.

Example implementation:

```python
import winreg

def get_installed_apps():
    apps = []
    path = r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall"

    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)

    for i in range(winreg.QueryInfoKey(key)[0]):
        subkey_name = winreg.EnumKey(key, i)
        subkey = winreg.OpenKey(key, subkey_name)

        try:
            name = winreg.QueryValueEx(subkey, "DisplayName")[0]
            apps.append(name)
        except:
            pass

    return apps
```

---

# macOS Implementation

Applications are typically located in:

```
/Applications
```

Example:

```python
import os

def get_installed_apps():
    apps = []
    for app in os.listdir("/Applications"):
        if app.endswith(".app"):
            apps.append(app.replace(".app",""))
    return apps
```

---

# Linux Implementation

Linux applications can be detected using:

```
/usr/share/applications
```

---

# 2. Environment Index

Once the scan completes, SUVI creates an index file.

Location:

```
suvi_environment.json
```

Example:

```json
{
 "installed_apps": [
  "Google Chrome",
  "Microsoft Edge",
  "Spotify"
 ],
 "browsers": [
  "Google Chrome",
  "Microsoft Edge"
 ],
 "music_players": [
  "Spotify"
 ]
}
```

This file is loaded every time SUVI starts.

---

# 3. Capability Mapper

The Capability Mapper converts raw apps into usable capabilities.

Example mapping:

| Capability      | Application |
| --------------- | ----------- |
| Web browsing    | Chrome      |
| Music streaming | Spotify     |
| Video playback  | VLC         |

Example output:

```json
{
 "capabilities": {
   "web_browser": "Google Chrome",
   "music_player": "Spotify",
   "video_player": "VLC"
 }
}
```

---

# 4. AI Context Injection

When SUVI sends a prompt to the Gemini orchestrator, the environment context is injected.

Example context:

```
SYSTEM ENVIRONMENT

Operating System: Windows 11

Installed Applications:
- Google Chrome
- Microsoft Edge
- Spotify

Available Browsers:
- Google Chrome
- Microsoft Edge

Available Music Players:
- Spotify

RULES

If a requested application is not installed,
use an available alternative.

Example:
User: "Play music on YouTube"
Action: Open browser → youtube.com
```

---

# Integration With SUVI Orchestrator

In `OrchestratorService`, environment data should be injected into prompts.

Example:

```python
environment = load_environment()

prompt = f"""
User request: {user_input}

System Environment:
Installed Apps: {environment['installed_apps']}
Browsers: {environment['browsers']}
Music Players: {environment['music_players']}

Choose actions that are possible on this system.
"""
```

---

# 5. Runtime Verification Layer

Before executing any action, SUVI verifies the environment.

Example:

Requested action:

```
launch_app("YouTube")
```

Check:

```
Is YouTube installed?
```

If not:

Fallback:

```
open_url("https://youtube.com")
```

Example implementation:

```python
def launch_app(app_name):
    if app_name not in installed_apps:
        return "APP_NOT_FOUND"

    subprocess.Popen(app_name)
```

---

# 6. Fallback Logic

SUVI should support fallback strategies.

Example:

User request:
"Play music."

Decision tree:

1. Spotify installed → open Spotify
2. Browser installed → open YouTube
3. Otherwise → ask user what to install

---

# 7. Dynamic Environment Updates

The environment should update when:

* A new application is installed
* SUVI restarts
* The user requests a refresh

Command example:

```
Hey SUVI
Refresh system environment
```

---

# 8. Security Considerations

Environment data is stored locally.

Never send the entire system environment to external servers.

Only send minimal context to the AI model.

---

# 9. Benefits

Environment awareness provides:

* Reduced hallucinations
* Better decision making
* Faster task execution
* Personalized AI behavior
* Higher reliability

---

# Example Full Flow

User command:

```
Hey SUVI
Play lofi music
```

Environment context:

```
Spotify installed
Chrome installed
```

Decision:

```
open Spotify
search "lofi music"
```

If Spotify not installed:

```
open Chrome
navigate to youtube.com
search "lofi music"
```

---

# Future Improvements

Possible extensions include:

* Running application detection
* Open window tracking
* Browser tab awareness
* File system indexing

These features would allow SUVI to understand the **entire state of the computer**.

---

# Summary

The Environment Awareness System enables SUVI to reason about the real computer environment.

This transforms SUVI from a generic AI assistant into a **true intelligent desktop agent**.

The system:

1. Scans the environment
2. Creates a capability map
3. Injects environment context into AI prompts
4. Verifies actions before execution
5. Uses fallback strategies

This significantly improves reliability, accuracy, and user experience.


