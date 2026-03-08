# SUVI — Gemini CLI Master Implementation Document

# Gemini Live Agent Challenge 2025 | Deadline: March 16, 2026

---

## CONTEXT FOR GEMINI CLI

You are helping build **SUVI** (Superintelligent Unified Voice Interface) — a production-grade AI agent that controls a user's desktop using natural voice and text. This document is the complete blueprint. Follow it precisely. Ask clarifying questions only when something is genuinely ambiguous. Always write complete, runnable code — never stubs or placeholders.

The developer has 5 days. Prioritize ruthlessly: working core loop first, polish second.

---

## HACKATHON ALIGNMENT (READ THIS FIRST)

**Competition:** Gemini Live Agent Challenge by Google on Devpost  
**Deadline:** March 16, 2026 @ 5:00pm PDT  
**Prize:** $25,000 Grand Prize + $10,000 Best UI Navigator = $35,000 target  

**Primary Category:** UI Navigator — "Build an agent that becomes the user's hands on screen. The agent observes the display, interprets visual elements WITHOUT relying on APIs or DOM access, and performs actions based on user intent."

**Secondary Category:** Live Agents — "Real-time audio/vision interaction. Users can talk naturally and interrupt."

**SUVI covers BOTH categories simultaneously.** This is the competitive advantage.

### Judging Criteria (memorize these weights)

- **Innovation & Multimodal UX: 40%** — Break the text-box paradigm. Must feel "Live" and context-aware, not turn-based.
- **Technical Architecture: 30%** — ADK + GenAI SDK + GCP hosting. Handle errors gracefully. Evidence of grounding.
- **Demo & Presentation: 30%** — Real working software in video. Architecture diagram. GCP proof.

### Mandatory Requirements

1. Gemini model ✓
2. Google GenAI SDK **OR** ADK ✓  (we use BOTH for maximum points)
3. At least one Google Cloud service ✓  (we use 6+)
4. Agents hosted on Google Cloud ✓

### Submission Checklist (build with this in mind from Day 1)

- [ ] Public GitHub repo with spin-up README
- [ ] GCP proof: screen recording of Cloud Run logs OR code file showing Vertex AI API calls
- [ ] Architecture diagram image (will be in `/docs/architecture.png`)
- [ ] Demo video < 4 minutes — real software, no mockups
- [ ] Text description of features + technologies + learnings

### Bonus Points (do all three)

- [ ] Blog post / Dev.to article with hashtag `#GeminiLiveAgentChallenge`
- [ ] Terraform IaC in `/infrastructure/terraform/`
- [ ] Join Google Developer Group → <https://gdg.community.dev/>

---

## WHAT SUVI DOES (THE PRODUCT VISION)

SUVI is a desktop AI agent that sees your screen, hears your voice, and executes actions — just like having a skilled assistant sitting next to you who can operate any software.

**Demo-worthy examples for the video:**

1. User says: "Book a meeting with Rahul next Tuesday at 3pm" → SUVI opens Google Calendar, creates event, finds Rahul's email, invites him — all by seeing the screen.
2. User says: "Summarize that email and reply saying I'll get back tomorrow" → SUVI reads Gmail on screen, types a reply.
3. User says: "Open VS Code, create a new Python file called data_processor.py and write a function to read a CSV" → SUVI does it.
4. User says: "Stop, that's the wrong file" → SUVI stops mid-action. *This is the interrupt capability judges want.*

**Key differentiator:** SUVI uses **Gemini 2.5 Computer Use** — a specialized model just released by Google for interpreting screenshots and generating executable computer actions. No other hackathon submission will be using this model. This alone puts SUVI in a different category.

---

## ARCHITECTURE DECISION (FINAL — DO NOT CHANGE)

### The Core Loop

```
User Voice → Gemini Live API → Transcript
User Screen → python-mss → JPEG frame
Both inputs → Gemini 2.5 Computer Use → Action JSON
Action JSON → PyAutoGUI / Playwright → Desktop executes
Result → Gemini Live TTS → User hears response
Everything → Firestore + Cloud Logging → Persistence + Audit
```

### Layer Map

```
┌─────────────────────────────────────────────────────────┐
│   LAYER 1: LOCAL PYQT6 CLIENT  (Single Python Process)  │
│   ┌──────────────┐  ┌─────────────────┐  ┌──────────┐  │
│   │  Login UI    │  │  Float Widget   │  │ Executor │  │
│   │  (QDialog)   │  │  (Chat overlay) │  │PyAutoGUI │  │
│   └──────────────┘  └─────────────────┘  └──────────┘  │
│        ↕ Direct Python calls — NO IPC overhead          │
└────────────────────────┬────────────────────────────────┘
                         │ HTTPS/WSS
┌────────────────────────▼────────────────────────────────┐
│   LAYER 2: CLOUD RUN GATEWAY  (FastAPI — Python)        │
│   WebSocket proxy | Auth (Firebase JWT) | Rate limiter  │
│   Session manager | Pub/Sub publisher | Secret Manager  │
└────────────────────────┬────────────────────────────────┘
                         │ gRPC + REST
┌────────────────────────▼────────────────────────────────┐
│   LAYER 3: VERTEX AI  (ADK Agent Engine)                │
│   SUVI Orchestrator Agent (ADK + Gemini 2.5 Pro)        │
│   Tools: computer_use(), voice_respond(), recall()      │
│   Sub-model: gemini-2.5-computer-use for screen actions │
└────────────────────────┬────────────────────────────────┘
                         │ SDK
┌────────────────────────▼────────────────────────────────┐
│   LAYER 4: GCP DATA LAYER                               │
│   Firestore | Pub/Sub | BigQuery | Cloud Logging        │
│   Secret Manager | Cloud Storage | Cloud Monitoring     │
└─────────────────────────────────────────────────────────┘
```

### Why PyQt6 (No Electron / No IPC)

- Single Python process — UI, voice capture, screen capture, and action execution share one runtime
- Direct function call latency: ~0.001ms vs IPC socket: ~1-2ms per call
- Screen frame (200KB JPEG) lives in one heap — no duplication
- Simpler deployment: PyInstaller single binary, no Node.js runtime needed

---

## TECHNOLOGY STACK (EXACT VERSIONS)

### Models (use these exact model IDs)

```python
MODELS = {
    # Core computer vision + action model — THE key differentiator
    "computer_use":   "gemini-2.5-computer-use",
    
    # Real-time voice I/O — persistent WebSocket session
    "live":           "gemini-2.0-flash-live-001",
    
    # Orchestrator reasoning + planning
    "orchestrator":   "gemini-2.5-pro-preview-06-05",
    
    # Fast text tasks (summaries, email drafts)
    "flash":          "gemini-2.0-flash-001",
    
    # Embeddings for memory
    "embedding":      "text-embedding-004",
}
```

### Python Dependencies (apps/desktop/requirements.txt)

```
PyQt6>=6.7.0
qasync>=0.27.1
google-genai>=1.0.0
google-cloud-aiplatform>=1.60.0
google-adk>=0.1.0
google-cloud-firestore>=2.16.0
google-cloud-pubsub>=2.21.0
google-cloud-secret-manager>=2.20.0
google-cloud-logging>=3.10.0
pyautogui>=0.9.54
playwright>=1.44.0
python-mss>=9.0.2
sounddevice>=0.4.7
numpy>=1.26.0
Pillow>=10.3.0
pynput>=1.7.7
pvporcupine>=3.0.0
websockets>=12.0
firebase-admin>=6.5.0
pyinstaller>=6.6.0
```

### GCP Services Used (for maximum judging points)

```
1. Vertex AI Agent Engine  — SUVI Orchestrator ADK agent
2. Gemini Live API         — Voice I/O WebSocket session
3. Cloud Run               — FastAPI gateway (min_instances=1)
4. Firestore               — Session memory + user profiles
5. Cloud Pub/Sub           — Action telemetry events
6. BigQuery                — Action analytics (demo dashboard)
7. Cloud Logging           — Every desktop action audit trail
8. Secret Manager          — API keys + Firebase credentials
9. Cloud Storage           — Session recordings (GIF replay)
10. Cloud Monitoring       — Agent latency dashboards
```

---

## PROJECT FOLDER STRUCTURE

```
suvi/
│
├── apps/
│   ├── desktop/                        # PyQt6 client — LOCAL Python
│   │   ├── suvi/
│   │   │   ├── __main__.py             # python -m suvi entry point
│   │   │   ├── app.py                  # QApplication + qasync loop
│   │   │   ├── controller.py           # Connects UI ↔ services ↔ executor
│   │   │   │
│   │   │   ├── ui/
│   │   │   │   ├── login/
│   │   │   │   │   ├── login_window.py         # QMainWindow: Sign in / Sign up
│   │   │   │   │   ├── login_page.py           # Google OAuth + email/password
│   │   │   │   │   ├── signup_page.py          # New account creation
│   │   │   │   │   ├── settings_page.py        # Theme, hotkeys, permissions
│   │   │   │   │   ├── profile_page.py         # User profile, preferences
│   │   │   │   │   └── login_styles.py         # QSS stylesheet (dark theme)
│   │   │   │   │
│   │   │   │   └── widget/
│   │   │   │       ├── chat_widget.py          # Floating transparent overlay
│   │   │   │       ├── chat_painter.py         # QPainter rendering
│   │   │   │       ├── chat_animator.py        # QPropertyAnimation transitions
│   │   │   │       ├── voice_indicator.py      # Mic amplitude waveform bar
│   │   │   │       ├── message_bubble.py       # Chat message rendering
│   │   │   │       ├── action_preview.py       # "About to click X" preview card
│   │   │   │       ├── confirm_dialog.py       # Tier 3+ action confirmation
│   │   │   │       └── tray.py                 # QSystemTrayIcon
│   │   │   │
│   │   │   ├── services/                       # Async services (qasync)
│   │   │   │   ├── auth_service.py             # Firebase Auth client
│   │   │   │   ├── live_session.py             # Gemini Live API WebSocket
│   │   │   │   ├── computer_use_service.py     # Gemini 2.5 Computer Use
│   │   │   │   ├── gateway_client.py           # WebSocket → Cloud Run
│   │   │   │   └── memory_service.py           # Firestore local cache
│   │   │   │
│   │   │   ├── workers/                        # QThread background tasks
│   │   │   │   ├── voice_worker.py             # sounddevice mic capture
│   │   │   │   ├── wake_word_worker.py         # Porcupine + pynput hotkey
│   │   │   │   ├── screen_worker.py            # python-mss frame capture
│   │   │   │   └── replay_worker.py            # Session GIF recorder
│   │   │   │
│   │   │   ├── executor/                       # Desktop action execution
│   │   │   │   ├── action_executor.py          # Main dispatcher
│   │   │   │   ├── desktop.py                  # PyAutoGUI mouse/keyboard
│   │   │   │   ├── browser.py                  # Playwright browser control
│   │   │   │   ├── filesystem.py               # File operations
│   │   │   │   ├── sandbox.py                  # Subprocess script runner
│   │   │   │   ├── permissions.py              # 5-tier action validator
│   │   │   │   ├── undo_stack.py               # Reversible action buffer
│   │   │   │   └── kill_switch.py              # Emergency halt all tasks
│   │   │   │
│   │   │   └── resources/
│   │   │       ├── icons/                      # SVG icons for UI
│   │   │       └── styles/
│   │   │           ├── dark.qss                # Dark theme stylesheet
│   │   │           └── light.qss               # Light theme stylesheet
│   │   │
│   │   ├── requirements.txt
│   │   ├── suvi.spec                           # PyInstaller build spec
│   │   └── Makefile                            # make dev | make build | make test
│   │
│   ├── gateway/                                # Cloud Run — FastAPI
│   │   ├── main.py                             # FastAPI app entry
│   │   ├── routes/
│   │   │   ├── ws_proxy.py                     # WebSocket ↔ Gemini Live proxy
│   │   │   ├── sessions.py                     # Session CRUD
│   │   │   ├── actions.py                      # Push action commands to client
│   │   │   └── health.py                       # /health + /metrics
│   │   ├── middleware/
│   │   │   ├── auth.py                         # Firebase JWT validation
│   │   │   ├── rate_limiter.py                 # In-memory sliding window
│   │   │   └── cors.py                         # CORS config
│   │   ├── services/
│   │   │   ├── firestore.py                    # Session persistence
│   │   │   ├── pubsub.py                       # Telemetry events
│   │   │   ├── secrets.py                      # Secret Manager client
│   │   │   └── cloud_logging.py                # Action audit logs
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── cloudbuild.yaml
│   │
│   └── dashboard/                              # Next.js (optional — Day 5 only)
│       └── (minimal Next.js app for GCP metrics demo)
│
├── agents/                                     # Vertex AI ADK Agents
│   ├── orchestrator/
│   │   ├── agent.py                            # ADK Agent definition
│   │   ├── tools/
│   │   │   ├── computer_use_tool.py            # Calls Gemini 2.5 Computer Use
│   │   │   ├── voice_tool.py                   # TTS response generation
│   │   │   ├── memory_tool.py                  # Firestore read/write
│   │   │   └── web_search_tool.py              # Vertex AI grounded search
│   │   ├── system_prompt.py                    # SUVI's personality + instructions
│   │   ├── action_schema.py                    # Pydantic models for actions
│   │   └── deploy.py                           # Vertex AI Agent Engine deploy
│   │
│   └── shared/
│       ├── models.py                           # Shared Pydantic types
│       ├── permissions.py                      # Action tier constants
│       └── telemetry.py                        # BigQuery + Pub/Sub logging
│
├── infrastructure/
│   ├── terraform/
│   │   ├── main.tf                             # Root — required for bonus points
│   │   ├── variables.tf
│   │   └── modules/
│   │       ├── cloud_run.tf
│   │       ├── firestore.tf
│   │       ├── pubsub.tf
│   │       ├── bigquery.tf
│   │       ├── iam.tf
│   │       └── secrets.tf
│   ├── firestore.rules
│   └── setup_gcp.sh                           # One-shot project bootstrap
│
├── docs/
│   ├── architecture.png                        # REQUIRED for submission
│   ├── architecture.md
│   └── demo_script.md                          # 4-minute video script
│
├── .github/
│   └── workflows/
│       ├── deploy-gateway.yml
│       └── deploy-agents.yml
│
├── pyproject.toml                              # Root Python config
└── README.md                                   # Spin-up instructions — REQUIRED
```

---

## THE TWO UI COMPONENTS

### UI 1: Login & Settings Window (QMainWindow)

Full-screen window that opens on first launch. After login it minimizes to tray.

**Pages:**

1. **Login Page** — Google OAuth button (primary) + email/password form. Dark glassmorphism design.
2. **Signup Page** — Name, email, password. Validates in real-time.
3. **Home/Dashboard** — Shows SUVI status, last 10 actions, quick settings toggle.
4. **Settings Page** — Tabs:
   - General: Wake word toggle, hotkey config, startup behavior
   - Theme: Dark/Light/System + accent color picker (7 colors)
   - Permissions: Per-app permission tiers (show table with dropdowns)
   - Privacy: Screen recording consent, data retention (7/30/90 days)
   - About: Version, changelog, links
5. **Profile Page** — Display name, avatar, connected accounts, sign out.

**Design Language:**

```python
# QSS Dark Theme — apply to QApplication
DARK_THEME = """
QMainWindow, QDialog {
    background-color: #0F172A;
    color: #E2E8F0;
    font-family: 'Segoe UI', 'SF Pro Display', system-ui;
}
QPushButton#primary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #4F46E5, stop:1 #7C3AED);
    border: none; border-radius: 8px;
    padding: 10px 24px; color: white; font-weight: 600;
}
QPushButton#primary:hover { background: #4338CA; }
QLineEdit {
    background: #1E293B; border: 1px solid #334155;
    border-radius: 8px; padding: 10px 14px; color: #E2E8F0;
}
QLineEdit:focus { border-color: #4F46E5; }
"""
```

---

### UI 2: Floating Chat Widget (Always-On-Top Overlay)

The day-to-day interface. A small, semi-transparent chat bubble that sits in a corner of the screen. Inspired by having a conversation with an assistant — not a control panel.

**States:**

```
IDLE:       Small pill shape (280×52px), 85% opacity
            Shows: [🎙 Tap or say "Hey Suvi"] 
            Always on top, click-through for empty areas

LISTENING:  Pill expands (320×72px), opacity 100%
            Shows: Animated voice waveform (5 bars, amplitude-driven)
            Shows: Partial transcript in real-time as user speaks
            
THINKING:   Same size, shows: "Thinking..." + spinning dot (indigo)
            Active tool shown: "Using Computer Vision..."

EXECUTING:  Progress bar inside pill, shows current action text
            Shows: "Clicking Google Calendar..." / "Typing..."
            Cancel button (×) appears on right

RESULT:     Pill expands to show last N messages (chat bubble style)
            Auto-collapses to idle after 6 seconds
            User can scroll history or type follow-up

ERROR:      Red accent border flash, error message, auto-recovers
```

**Widget Implementation Pattern:**

```python
# apps/desktop/suvi/ui/widget/chat_widget.py

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal, pyqtProperty
from PyQt6.QtGui import QPainter, QPainterPath, QColor, QBrush, QFont
import math

class ChatWidget(QWidget):
    # Signals from UI to controller
    user_text_submitted = pyqtSignal(str)
    cancel_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self._setup_window()
        self._state = "idle"
        self._transcript = ""
        self._messages = []        # List of {role, text, timestamp}
        self._amplitude = 0.0      # 0.0-1.0 driven by mic level
        self._progress = 0.0       # 0.0-1.0 action progress
        self._action_text = ""     # Current action description
        self._setup_animations()
        self._setup_input()

    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedWidth(320)
        self._place_bottom_right()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background pill
        bg = QColor(15, 23, 42, 220)   # #0F172A at 86% opacity
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 28, 28)
        p.fillPath(path, QBrush(bg))
        
        # Accent border (state-dependent color)
        border_color = {
            "idle":      QColor(79, 70, 229, 180),    # indigo
            "listening": QColor(16, 185, 129, 255),   # green
            "thinking":  QColor(79, 70, 229, 255),    # indigo
            "executing": QColor(245, 158, 11, 255),   # amber
            "error":     QColor(220, 38, 38, 255),    # red
        }.get(self._state, QColor(79, 70, 229, 180))
        
        pen = p.pen()
        pen.setColor(border_color)
        pen.setWidth(2)
        p.setPen(pen)
        p.drawPath(path)
        
        # State-specific content
        if self._state == "listening":
            self._draw_waveform(p)
        elif self._state in ("thinking", "executing"):
            self._draw_status(p)
        elif self._state in ("result", "idle"):
            self._draw_messages(p)
            
    def _draw_waveform(self, p):
        """5-bar mic amplitude visualizer"""
        bars = 7
        cx = self.width() / 2
        cy = self.height() / 2
        bar_w = 4
        gap = 6
        total_w = bars * (bar_w + gap)
        x_start = cx - total_w / 2
        
        for i in range(bars):
            # Each bar has phase-shifted amplitude
            phase = math.sin(self._amplitude * math.pi * 2 + i * 0.8)
            h = max(8, int(self.height() * 0.5 * abs(phase) * self._amplitude + 8))
            x = x_start + i * (bar_w + gap)
            y = cy - h / 2
            color = QColor(16, 185, 129, 220)
            p.setBrush(QBrush(color))
            p.setPen(Qt.PenStyle.NoPen)
            path = QPainterPath()
            path.addRoundedRect(x, y, bar_w, h, 2, 2)
            p.fillPath(path, QBrush(color))
```

---

## CORE IMPLEMENTATION: GEMINI COMPUTER USE

This is the heart of SUVI and the hackathon differentiator.

```python
# apps/desktop/suvi/services/computer_use_service.py

import asyncio
import base64
import io
from dataclasses import dataclass
from typing import Optional
from google import genai
from google.genai import types
import pyautogui
import mss
from PIL import Image

@dataclass
class ComputerAction:
    """Structured action from Gemini 2.5 Computer Use"""
    action_type: str      # click, type, scroll, hotkey, screenshot, done
    x: Optional[int] = None
    y: Optional[int] = None
    text: Optional[str] = None
    keys: Optional[list] = None
    direction: Optional[str] = None
    amount: Optional[int] = None
    description: str = ""    # Human-readable action description

class ComputerUseService:
    """
    Drives the Gemini 2.5 Computer Use model.
    
    The loop:
    1. Capture screenshot
    2. Send to gemini-2.5-computer-use with user intent
    3. Parse action response
    4. Execute action via PyAutoGUI
    5. Capture new screenshot
    6. Repeat until model says 'done' or user interrupts
    """

    def __init__(self, client: genai.Client, firestore_service, logger):
        self.client = client
        self.firestore = firestore_service
        self.logger = logger
        self._active = False
        self._interrupt_requested = False

    def interrupt(self):
        """Called when user says 'stop' or clicks cancel"""
        self._interrupt_requested = True

    async def execute_task(
        self,
        intent: str,
        user_id: str,
        session_id: str,
        on_action: callable = None,     # Callback: (action_description) -> None
        on_screenshot: callable = None,  # Callback: (jpeg_bytes) -> None
    ) -> dict:
        """
        Main computer use loop.
        Returns dict: {success, actions_taken, final_screenshot, error}
        """
        self._active = True
        self._interrupt_requested = False
        actions_taken = []
        max_steps = 15  # Safety: prevent infinite loops
        
        screenshot = self._capture_screen()
        
        for step in range(max_steps):
            if self._interrupt_requested:
                return {"success": False, "reason": "user_interrupted",
                        "actions_taken": actions_taken}
            
            if on_screenshot:
                on_screenshot(screenshot)
            
            # Build the prompt with current screenshot
            response = await self._call_computer_use(intent, screenshot, actions_taken)
            
            if response is None:
                break
                
            action = self._parse_action(response)
            
            if action.action_type == "done":
                await self._log_to_cloud(user_id, session_id, actions_taken, "success")
                return {"success": True, "actions_taken": actions_taken,
                        "final_screenshot": screenshot}
            
            # Safety check before executing
            if not self._is_safe_action(action):
                return {"success": False, "reason": "safety_blocked",
                        "action": action.description}
            
            if on_action:
                on_action(action.description)
            
            # Execute the action
            await self._execute_action(action)
            actions_taken.append({
                "step": step + 1,
                "action": action.action_type,
                "description": action.description,
            })
            
            # Brief wait for UI to update before next screenshot
            await asyncio.sleep(0.5)
            screenshot = self._capture_screen()
        
        return {"success": False, "reason": "max_steps_reached",
                "actions_taken": actions_taken}

    async def _call_computer_use(self, intent: str, screenshot: bytes, history: list) -> Optional[str]:
        history_text = "\n".join([
            f"Step {h['step']}: {h['description']}" for h in history
        ]) if history else "No actions taken yet."
        
        prompt = f"""You are controlling a computer to help a user. 

User intent: {intent}

Actions already taken:
{history_text}

Look at the current screenshot carefully. Determine the NEXT single action to take.

Respond with EXACTLY ONE of these formats:
CLICK: x=<number> y=<number> reason=<why>
TYPE: text=<text to type> reason=<why>
HOTKEY: keys=<key+key> reason=<why>
SCROLL: direction=<up/down> amount=<1-10> reason=<why>
SCREENSHOT: reason=<why you need to see more>
DONE: reason=<task completed or cannot proceed>

Be precise with coordinates. Look for UI elements carefully."""

        try:
            response = await self.client.aio.models.generate_content(
                model="gemini-2.5-computer-use",
                contents=[
                    {
                        "role": "user",
                        "parts": [
                            {"inline_data": {"mime_type": "image/jpeg", "data": screenshot}},
                            {"text": prompt}
                        ]
                    }
                ],
                config=types.GenerateContentConfig(
                    temperature=0.1,   # Low temp for precise actions
                    max_output_tokens=512,
                )
            )
            return response.text
        except Exception as e:
            self.logger.error(f"Computer use API error: {e}")
            return None

    def _parse_action(self, response_text: str) -> ComputerAction:
        text = response_text.strip().upper()
        
        if text.startswith("CLICK:"):
            parts = response_text.split()
            x = int([p for p in parts if p.startswith("x=")][0].split("=")[1])
            y = int([p for p in parts if p.startswith("y=")][0].split("=")[1])
            reason_start = response_text.find("reason=")
            reason = response_text[reason_start + 7:] if reason_start > -1 else ""
            return ComputerAction("click", x=x, y=y, description=f"Click at ({x},{y}): {reason}")
            
        elif text.startswith("TYPE:"):
            text_start = response_text.find("text=") + 5
            text_end = response_text.find(" reason=")
            typed = response_text[text_start:text_end if text_end > -1 else None]
            typed = typed.strip().strip('"')
            return ComputerAction("type", text=typed, description=f"Type: {typed[:50]}")
            
        elif text.startswith("HOTKEY:"):
            keys_start = response_text.find("keys=") + 5
            keys_end = response_text.find(" reason=")
            keys_str = response_text[keys_start:keys_end if keys_end > -1 else None].strip()
            keys = keys_str.split("+")
            return ComputerAction("hotkey", keys=keys, description=f"Hotkey: {keys_str}")
            
        elif text.startswith("SCROLL:"):
            direction = "down" if "down" in text else "up"
            return ComputerAction("scroll", direction=direction, amount=3,
                                  description=f"Scroll {direction}")
            
        elif text.startswith("DONE:"):
            reason = response_text[5:].strip()
            return ComputerAction("done", description=reason)
            
        else:
            return ComputerAction("done", description="Unrecognized response — stopping")

    async def _execute_action(self, action: ComputerAction):
        if action.action_type == "click":
            pyautogui.click(action.x, action.y)
        elif action.action_type == "type":
            pyautogui.write(action.text, interval=0.03)
        elif action.action_type == "hotkey":
            pyautogui.hotkey(*action.keys)
        elif action.action_type == "scroll":
            clicks = action.amount if action.direction == "up" else -action.amount
            pyautogui.scroll(clicks)

    def _capture_screen(self) -> bytes:
        with mss.mss() as sct:
            frame = sct.grab(sct.monitors[1])
        img = Image.frombytes("RGB", frame.size, frame.bgra, "raw", "BGRX")
        # Resize to 1366px wide (good balance of quality vs token cost)
        w, h = img.size
        if w > 1366:
            img = img.resize((1366, int(1366 * h / w)), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=85)
        return base64.b64encode(buf.getvalue()).decode()

    def _is_safe_action(self, action: ComputerAction) -> bool:
        # Block dangerous coordinates (e.g., system areas)
        if action.action_type == "click":
            if action.y and action.y < 30:   # Menu bar — be cautious
                return True   # Allow but could add confirm dialog
        if action.action_type == "type":
            # Block shell injection attempts
            dangerous = ["rm -rf", "format c:", "del /s", "sudo rm"]
            if action.text and any(d in action.text.lower() for d in dangerous):
                return False
        return True

    async def _log_to_cloud(self, user_id, session_id, actions, status):
        """Log to Cloud Logging and Pub/Sub for demo evidence"""
        import google.cloud.logging as cloud_logging
        # This creates the audit trail shown in demo
        pass

    def _capture_screen(self) -> str:
        with mss.mss() as sct:
            frame = sct.grab(sct.monitors[1])
        img = Image.frombytes("RGB", frame.size, frame.bgra, "raw", "BGRX")
        w, h = img.size
        if w > 1366:
            img = img.resize((1366, int(1366 * h / w)), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=85)
        return base64.b64encode(buf.getvalue()).decode()
```

---

## CORE IMPLEMENTATION: GEMINI LIVE API (Voice I/O)

```python
# apps/desktop/suvi/services/live_session.py

import asyncio
import sounddevice as sd
import numpy as np
import qasync
from google import genai
from google.genai import types
from PyQt6.QtCore import QObject, pyqtSignal

SUVI_SYSTEM_PROMPT = """You are SUVI — a precise, friendly AI assistant that controls the user's computer.

Your personality:
- Confident but warm. You speak like a skilled colleague, not a robot.
- Brief verbal confirmations: "On it.", "Done.", "Got it, one moment."
- When you need to take multiple steps, briefly narrate: "Opening Calendar now..."
- When interrupted, acknowledge: "Of course, stopping."
- When you can't do something safely, say why clearly.

Your capabilities:
- You can SEE the user's screen in real-time
- You can CLICK, TYPE, SCROLL on any application
- You can SEARCH the web, READ documents on screen
- You can EXECUTE multi-step workflows autonomously

Safety rules you always follow:
- Never delete files without explicit confirmation
- Never send emails without user approval
- Never access password fields or financial data
- Always confirm before system-level changes

When you receive a task:
1. Briefly confirm you understand it
2. Narrate your first action
3. Execute via computer use
4. Confirm completion or ask for clarification"""

class GeminiLiveService(QObject):
    # Signals to ChatWidget — thread-safe
    transcript_ready   = pyqtSignal(str, bool)   # (text, is_final)
    response_audio     = pyqtSignal(bytes)         # TTS audio chunk
    state_changed      = pyqtSignal(str)           # "listening"/"thinking"/"done"
    amplitude_updated  = pyqtSignal(float)         # 0.0-1.0 for waveform

    def __init__(self, client: genai.Client):
        super().__init__()
        self.client = client
        self._session = None
        self._running = False
        self._interrupt_flag = False

    def interrupt(self):
        self._interrupt_flag = True

    async def start(self, user_profile: dict):
        """Start persistent Gemini Live session"""
        self._running = True
        
        # Inject user profile into system prompt
        profile_context = f"\nUser: {user_profile.get('name', 'User')}. Preferences: {user_profile.get('preferences', {})}"
        
        config = types.LiveConnectConfig(
            model="gemini-2.0-flash-live-001",
            response_modalities=["AUDIO", "TEXT"],
            system_instruction=types.Content(
                parts=[types.Part(text=SUVI_SYSTEM_PROMPT + profile_context)]
            ),
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Aoede"   # Best voice for assistant persona
                    )
                )
            ),
            context_window_compression=types.ContextWindowCompressionConfig(
                trigger_tokens=28000,
                target_tokens=14000,
            ),
        )
        
        async with self.client.aio.live.connect(
            model="gemini-2.0-flash-live-001",
            config=config
        ) as session:
            self._session = session
            await asyncio.gather(
                self._stream_mic(session),
                self._receive_responses(session),
            )

    async def inject_screen_frame(self, jpeg_base64: str):
        """Inject current screen state into Live session context"""
        if self._session:
            import base64
            await self._session.send(
                input=types.LiveClientRealtimeInput(
                    media_chunks=[
                        types.Blob(
                            data=base64.b64decode(jpeg_base64),
                            mime_type="image/jpeg"
                        )
                    ]
                )
            )

    async def send_text(self, text: str):
        """Send text message to session"""
        if self._session:
            await self._session.send(input=text, end_of_turn=True)

    async def _stream_mic(self, session):
        """Capture mic and stream to Gemini Live"""
        SAMPLE_RATE = 16000
        CHUNK_MS = 100
        CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_MS / 1000)
        
        def audio_callback(indata, frames, time, status):
            if self._interrupt_flag:
                return
            chunk = (indata[:, 0] * 32767).astype(np.int16).tobytes()
            amplitude = float(np.abs(indata).mean())
            self.amplitude_updated.emit(min(amplitude * 10, 1.0))
            asyncio.get_event_loop().call_soon_threadsafe(
                lambda: asyncio.ensure_future(
                    session.send(
                        input=types.LiveClientRealtimeInput(
                            media_chunks=[types.Blob(data=chunk, mime_type="audio/pcm;rate=16000")]
                        )
                    )
                )
            )
        
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype=np.float32,
            blocksize=CHUNK_SAMPLES,
            callback=audio_callback
        ):
            while self._running:
                await asyncio.sleep(0.1)

    async def _receive_responses(self, session):
        """Process responses from Gemini Live"""
        async for response in session.receive():
            if self._interrupt_flag:
                self._interrupt_flag = False
                self.state_changed.emit("idle")
                continue
                
            if response.server_content:
                content = response.server_content
                
                # Text (transcript or narration)
                if content.model_turn:
                    for part in content.model_turn.parts:
                        if part.text:
                            self.transcript_ready.emit(part.text, True)
                            self.state_changed.emit("thinking")
                
                # Audio (TTS)
                if hasattr(content, 'audio') and content.audio:
                    self.response_audio.emit(content.audio.data)
                
                # Turn complete
                if content.turn_complete:
                    self.state_changed.emit("done")
```

---

## CORE IMPLEMENTATION: ADK ORCHESTRATOR

```python
# agents/orchestrator/agent.py

from google.adk import Agent, Tool
from google.adk.runners import VertexAIRunner
from google.cloud import aiplatform, firestore
from .tools.computer_use_tool import computer_use_tool
from .tools.memory_tool import memory_tool
from .tools.web_search_tool import web_search_tool
from .system_prompt import ORCHESTRATOR_SYSTEM_PROMPT

# Register tools
@Tool(
    name="execute_computer_task",
    description="Execute a visual computer task by taking screenshots and performing actions on the user's desktop. Use this for any task that requires interacting with the computer UI.",
)
async def execute_computer_task(
    task_description: str,
    user_id: str,
    session_id: str,
) -> dict:
    """Calls the computer use pipeline and returns results"""
    return await computer_use_tool(task_description, user_id, session_id)

@Tool(
    name="recall_context",
    description="Retrieve relevant past interactions, user preferences, or previously completed tasks from memory.",
)
async def recall_context(query: str, user_id: str) -> str:
    return await memory_tool.search(query, user_id)

@Tool(
    name="search_web",
    description="Search the web for current information to ground responses.",
)
async def search_web(query: str) -> str:
    return await web_search_tool.search(query)

# Create ADK Agent
suvi_agent = Agent(
    name="suvi-orchestrator",
    model="gemini-2.5-pro-preview-06-05",
    description="SUVI is an AI agent that controls the user's desktop using vision and natural language.",
    instruction=ORCHESTRATOR_SYSTEM_PROMPT,
    tools=[execute_computer_task, recall_context, search_web],
)

# Deploy to Vertex AI
def deploy():
    runner = VertexAIRunner(
        project=GCP_PROJECT_ID,
        location="us-central1",
        staging_bucket=f"gs://{GCP_PROJECT_ID}-suvi-staging",
    )
    runner.deploy(
        agent=suvi_agent,
        display_name="SUVI Orchestrator",
        description="Main SUVI orchestrator agent — deployed via ADK",
    )
    print("SUVI Orchestrator deployed to Vertex AI Agent Engine")

if __name__ == "__main__":
    deploy()
```

---

## CLOUD RUN GATEWAY

```python
# apps/gateway/main.py

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from routes import ws_proxy, sessions, actions, health
from middleware.auth import verify_firebase_token
from services.firestore import FirestoreService
from services.cloud_logging import ActionLogger

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize services
    app.state.firestore = FirestoreService()
    app.state.logger = ActionLogger()
    print("SUVI Gateway started — Cloud Run instance ready")
    yield
    print("SUVI Gateway shutting down")

app = FastAPI(
    title="SUVI Gateway",
    description="Cloud Run gateway — WebSocket proxy, auth, session management",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Lock down in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ws_proxy.router, prefix="/ws")
app.include_router(sessions.router, prefix="/sessions")
app.include_router(actions.router, prefix="/actions")
app.include_router(health.router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=False)
```

```python
# apps/gateway/routes/ws_proxy.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from google import genai
from google.genai import types
import asyncio
import json

router = APIRouter()
active_connections: dict[str, WebSocket] = {}   # session_id → client WebSocket

@router.websocket("/session/{session_id}")
async def websocket_session(websocket: WebSocket, session_id: str):
    """
    Proxies bidirectional WebSocket:
    - Incoming from client: audio chunks + screen frames
    - Outgoing to client: transcripts + TTS audio + action commands
    Also broadcasts action commands from Vertex AI agents back to client.
    """
    await websocket.accept()
    active_connections[session_id] = websocket
    
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
                
            elif msg_type == "action_command":
                # Forward action commands to client (from Vertex AI agent)
                await websocket.send_json(data)
                
            elif msg_type == "session_event":
                # Log to Pub/Sub for telemetry
                pass
                
    except WebSocketDisconnect:
        del active_connections[session_id]
```

---

## FIRESTORE SCHEMA

```
Collection: users/{userId}
  Document: profile
    - name: string
    - email: string
    - avatar_url: string
    - created_at: timestamp
    - preferences: {
        theme: "dark" | "light" | "system",
        wake_word_enabled: bool,
        hotkey: string,
        widget_position: {x: int, y: int},
        permission_level_default: 1-4,
        accent_color: string,
      }

Collection: sessions/{sessionId}
  - user_id: string
  - started_at: timestamp
  - ended_at: timestamp | null
  - message_count: int
  - actions_taken: int
  - agent_used: string

Collection: sessions/{sessionId}/messages/{messageId}
  - role: "user" | "assistant"
  - text: string
  - timestamp: timestamp
  - actions: array of {type, description, success}
  - screenshot_ref: string (Cloud Storage path, optional)

Collection: sessions/{sessionId}/actions/{actionId}
  - step: int
  - action_type: string
  - description: string
  - success: bool
  - timestamp: timestamp
  - screenshot_before_ref: string
  - screenshot_after_ref: string
```

---

## 5-DAY BUILD PLAN

### Day 1 — Foundation (Most Important Day)

**Goal: Working screen capture → Gemini Computer Use → PyAutoGUI loop**

Morning (4h):

1. `setup_gcp.sh` — Create GCP project, enable APIs, create service account
2. `apps/desktop/suvi/__main__.py` + `app.py` — PyQt6 app skeleton with qasync
3. `apps/desktop/suvi/services/computer_use_service.py` — Full implementation
4. Test the computer use loop with a simple hardcoded intent ("open Chrome")

Afternoon (4h):
5. `apps/desktop/suvi/executor/` — PyAutoGUI + Playwright action executor
6. `apps/desktop/suvi/workers/screen_worker.py` — mss screen capture QThread
7. `apps/desktop/suvi/workers/wake_word_worker.py` — Porcupine + pynput hotkey
8. End of Day 1 milestone: Say "open Chrome" → SUVI opens Chrome

---

### Day 2 — Voice + Memory

**Goal: Working Gemini Live voice conversation with screen context**

Morning (4h):

1. `apps/desktop/suvi/services/live_session.py` — Full Gemini Live implementation
2. `apps/desktop/suvi/workers/voice_worker.py` — sounddevice mic QThread
3. Wire up voice → live session → computer use (the full loop)
4. Test: Speak a task → SUVI executes it

Afternoon (4h):
5. Firebase Auth setup (Google OAuth)
6. `apps/desktop/suvi/services/auth_service.py` — Firebase client
7. `apps/desktop/suvi/services/memory_service.py` — Firestore session logging
8. Test the full loop with memory persistence

---

### Day 3 — Cloud Infrastructure + Gateway

**Goal: All GCP services connected and provable for submission**

Morning (4h):

1. `apps/gateway/` — FastAPI Cloud Run service
2. Deploy gateway to Cloud Run: `gcloud run deploy suvi-gateway`
3. `agents/orchestrator/` — ADK agent, deploy to Vertex AI Agent Engine
4. Wire local app → Cloud Run gateway → Vertex AI

Afternoon (4h):
5. Firestore rules + indexes
6. Cloud Pub/Sub topics (action telemetry)
7. BigQuery dataset + table for action logs
8. `infrastructure/terraform/` — IaC for bonus points
9. Cloud Logging — verify action audit trail shows in console

---

### Day 4 — UI Polish + Features

**Goal: Both UIs complete, feature set demo-worthy**

Morning (4h):

1. `apps/desktop/suvi/ui/login/` — Login window (Google OAuth + settings)
2. `apps/desktop/suvi/ui/widget/` — Floating chat widget complete
3. Theme system (dark/light) + accent color
4. Action confirmation dialogs for Tier 3+ actions

Afternoon (4h):
5. **Autopilot Mode** — multi-step task execution without confirmation
6. **SUVI Replay** — save session as GIF to Cloud Storage
7. **Smart Interrupt** — user can say "stop" mid-task
8. Integration test: 5 different demo scenarios

---

### Day 5 — Demo + Submission

**Goal: Win-ready submission**

Morning (4h):

1. Record demo video (4 minutes):
   - 0:00-0:45 — Problem intro + SUVI overview
   - 0:45-1:30 — Demo #1: "Book a meeting with Rahul" (calendar workflow)
   - 1:30-2:15 — Demo #2: "Summarize that email and reply" (Gmail)
   - 2:15-3:00 — Demo #3: Voice interrupt mid-task (shows real-time capability)
   - 3:00-3:45 — Architecture walkthrough + GCP dashboard proof
   - 3:45-4:00 — Closing + SUVI's name reveal story (human touch)
2. Architecture diagram (draw.io or Excalidraw) — export as PNG

Afternoon (4h):
3. README.md — Complete spin-up instructions
4. GCP proof screen recording (Cloud Run logs + Vertex AI usage)
5. Blog post draft for bonus points
6. Devpost submission — fill all fields carefully
7. Submit before 5pm PDT

---

## KEY WINNING FEATURES TO IMPLEMENT

### Feature 1: Smart Interrupt (40% judging weight — Innovation)

The hackathon criteria explicitly mention "can be interrupted." This is critical.

```python
# In live_session.py — handle interruption keyword
async def _receive_responses(self, session):
    async for response in session.receive():
        if response.server_content and response.server_content.interrupted:
            # User interrupted — stop computer use task
            self.computer_use.interrupt()
            self.state_changed.emit("idle")
            continue
```

### Feature 2: SUVI Replay (Demo Showstopper)

Save every session as an animated GIF → upload to Cloud Storage → shareable URL.
This becomes PROOF for the submission and a viral demo moment.

```python
# apps/desktop/suvi/workers/replay_worker.py
class ReplayWorker(QThread):
    """Accumulates screenshots during a task and saves as GIF"""
    replay_saved = pyqtSignal(str)   # Cloud Storage URL
    
    def __init__(self):
        super().__init__()
        self._frames = []
    
    def add_frame(self, jpeg_bytes: bytes):
        self._frames.append(Image.open(io.BytesIO(jpeg_bytes)))
    
    def save_replay(self, session_id: str):
        if not self._frames:
            return
        gif_path = f"/tmp/suvi_replay_{session_id}.gif"
        self._frames[0].save(
            gif_path,
            save_all=True,
            append_images=self._frames[1:],
            duration=500,   # 500ms per frame
            loop=0,
            optimize=True,
        )
        # Upload to Cloud Storage
        # url = upload_to_gcs(gif_path, f"replays/{session_id}.gif")
        # self.replay_saved.emit(url)
```

### Feature 3: Autopilot Mode

User says "Hey Suvi, autopilot on" — SUVI executes multi-step tasks without asking for confirmation on Tier 1-2 actions. Shows up in the demo as truly autonomous behavior.

### Feature 4: Universal App Control Message

In your demo description, make it explicit: **SUVI works on ANY application without requiring API access or DOM access.** It only uses vision. This directly addresses the UI Navigator judging criteria and makes SUVI fundamentally different from browser extension-based competitors.

### Feature 5: Context Memory in Conversation

SUVI knows what you were doing: "Yesterday we were working on the budget spreadsheet — want me to open that?" — Pulled from Firestore session history.

---

## ENVIRONMENT VARIABLES (.env)

```bash
# Google Cloud
GCP_PROJECT_ID=suvi-hackathon-2025
GCP_LOCATION=us-central1
GCP_REGION=us-central1

# Gemini
GEMINI_API_KEY=<your_key>

# Firebase (for auth)
FIREBASE_PROJECT_ID=suvi-hackathon-2025
FIREBASE_WEB_API_KEY=<your_firebase_key>
FIREBASE_AUTH_DOMAIN=suvi-hackathon-2025.firebaseapp.com

# Cloud Run Gateway URL (after deployment)
GATEWAY_URL=https://suvi-gateway-xxxx-uc.a.run.app

# Porcupine (wake word)
PORCUPINE_ACCESS_KEY=<your_key>  # Free at picovoice.ai

# Feature flags
ENABLE_REPLAY=true
ENABLE_AUTOPILOT=false   # Enable in Day 4
ENABLE_SCREEN_RECORDING=true
```

---

## SETUP_GCP.SH (One-Shot Bootstrap)

```bash
#!/bin/bash
# infrastructure/setup_gcp.sh
# Run once: ./setup_gcp.sh your-project-id

PROJECT_ID=${1:-"suvi-hackathon-2025"}
REGION="us-central1"

echo "Setting up SUVI GCP project: $PROJECT_ID"

gcloud projects create $PROJECT_ID --name="SUVI Hackathon" 2>/dev/null || true
gcloud config set project $PROJECT_ID

# Enable all required APIs
gcloud services enable \
  aiplatform.googleapis.com \
  run.googleapis.com \
  firestore.googleapis.com \
  pubsub.googleapis.com \
  bigquery.googleapis.com \
  logging.googleapis.com \
  secretmanager.googleapis.com \
  storage.googleapis.com \
  cloudbuild.googleapis.com \
  firebase.googleapis.com \
  identitytoolkit.googleapis.com

# Create service account
gcloud iam service-accounts create suvi-sa \
  --display-name="SUVI Service Account"

SA_EMAIL="suvi-sa@${PROJECT_ID}.iam.gserviceaccount.com"

# Grant roles
for role in \
  roles/aiplatform.user \
  roles/datastore.user \
  roles/pubsub.publisher \
  roles/bigquery.dataEditor \
  roles/logging.logWriter \
  roles/secretmanager.secretAccessor \
  roles/storage.objectCreator; do
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" --role="$role" --quiet
done

# Download credentials
gcloud iam service-accounts keys create credentials.json \
  --iam-account=$SA_EMAIL

# Create Firestore database
gcloud firestore databases create --location=$REGION --type=firestore-native

# Create Pub/Sub topics
for topic in suvi-actions suvi-sessions suvi-telemetry suvi-dlq; do
  gcloud pubsub topics create $topic
done

# Create BigQuery dataset
bq mk --dataset --location=$REGION ${PROJECT_ID}:suvi_analytics

# Create Cloud Storage bucket for replays
gsutil mb -l $REGION gs://${PROJECT_ID}-suvi-replays

echo "GCP setup complete!"
echo "SA credentials saved to credentials.json"
echo "Set GOOGLE_APPLICATION_CREDENTIALS=./credentials.json"
```

---

## README.MD TEMPLATE (Required for Submission)

```markdown
# SUVI — Superintelligent Unified Voice Interface

> An AI agent that sees your screen, hears your voice, and takes action.
> Built for the Google Gemini Live Agent Challenge 2025.

## Demo

[4-minute demo video](link)
[Architecture diagram](docs/architecture.png)

## What SUVI Does

SUVI uses Gemini 2.5 Computer Use to observe your desktop via screenshots
and execute actions — clicking, typing, scrolling — on any application,
without requiring any API access or DOM inspection. You talk to SUVI
naturally; it handles the rest.

**Example tasks:**
- "Book a meeting with Rahul next Tuesday at 3pm"
- "Summarize that email and draft a reply"
- "Open VS Code and write a function to parse JSON"
- (Say "stop" at any point to interrupt)

## Google Technologies Used

| Technology | Usage |
|---|---|
| Gemini 2.5 Computer Use | Core screen understanding + action generation |
| Gemini Live API | Real-time voice I/O (voice_name: Aoede) |
| Google ADK | SUVI Orchestrator agent framework |
| Vertex AI Agent Engine | ADK agent hosting |
| Cloud Run | FastAPI gateway (WebSocket proxy + auth) |
| Firestore | Session memory + user profiles |
| Cloud Pub/Sub | Action telemetry events |
| BigQuery | Analytics + action history |
| Cloud Logging | Audit trail for all desktop actions |
| Secret Manager | API key management |

## Architecture

See [docs/architecture.png](docs/architecture.png)

## Quick Start (5 minutes)

### Prerequisites
- Python 3.12+
- Google Cloud project with billing enabled
- GCP credentials (service account JSON)

### 1. Clone & Install

```bash
git clone https://github.com/yourusername/suvi.git
cd suvi
python -m venv .venv && source .venv/bin/activate
pip install -r apps/desktop/requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your GCP_PROJECT_ID, GEMINI_API_KEY, etc.
```

### 3. Bootstrap GCP (first time only)

```bash
chmod +x infrastructure/setup_gcp.sh
./infrastructure/setup_gcp.sh your-project-id
```

### 4. Deploy Gateway to Cloud Run

```bash
cd apps/gateway
gcloud run deploy suvi-gateway \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --min-instances 1
```

### 5. Deploy ADK Agent to Vertex AI

```bash
cd agents/orchestrator
python deploy.py
```

### 6. Run SUVI Desktop Client

```bash
cd apps/desktop
python -m suvi
```

## Cloud Deployment Proof

See [cloud_proof.mp4](docs/cloud_proof.mp4) — screen recording showing:

- Cloud Run suvi-gateway instance running
- Vertex AI Agent Engine suvi-orchestrator deployed
- Cloud Logging showing real-time action audit trail
- Firestore documents being written during a live session

## License

MIT

```

---

## ARCHITECTURE DIAGRAM DESCRIPTION
(For draw.io / Excalidraw — create this as your first visual asset)

**Title:** SUVI System Architecture — Gemini Live Agent Challenge 2025

**Elements to include:**
1. Left box: "Local Machine (PyQt6)" containing:
   - "Login Window" (purple)
   - "Floating Chat Widget" (purple)
   - "Voice Worker (sounddevice)" (gray)
   - "Screen Worker (python-mss)" (gray)
   - "Action Executor (PyAutoGUI)" (orange)
   
2. Center box: "Cloud Run Gateway (FastAPI)" containing:
   - "WebSocket Proxy"
   - "Firebase Auth"
   - "Session Manager"
   
3. Right box: "Vertex AI" containing:
   - "SUVI Orchestrator (ADK)"
   - "Gemini 2.5 Computer Use" (highlighted — key differentiator)
   - "Gemini Live API"
   
4. Bottom box: "GCP Data Layer" containing:
   - Firestore | Pub/Sub | BigQuery | Cloud Logging | Storage
   
5. Arrows:
   - Voice audio: Local → Cloud Run → Gemini Live API
   - Screen frames: Local → direct to Gemini Computer Use
   - Action commands: Vertex AI → Cloud Run → Local Executor
   - Telemetry: Everything → BigQuery + Cloud Logging

---

## DEMO VIDEO SCRIPT (4 minutes)

**0:00 — Hook (20s)**
"What if you could just tell your computer what you need, and it would do it — no shortcuts, no tutorials, just a conversation?"

**0:20 — Product intro (25s)**
Show SUVI floating widget idle on desktop. "This is SUVI. It sees your screen in real-time. It hears your voice. And it takes action — on any application, without any plugins or API access."

**0:45 — Demo 1: Calendar Booking (45s)**
Say: "Hey Suvi, book a meeting with Priya tomorrow at 2pm"
Show: SUVI opening Google Calendar, navigating to tomorrow, creating event, entering name
Widget shows transcript + "Clicking New Event..." action text

**1:30 — Demo 2: Email (45s)**
Say: "Summarize the last email from Vikram and draft a polite reply saying I need one more day"
Show: SUVI reading Gmail, reading email on screen, composing reply
End with: Widget shows "Draft ready — want me to send it?" → User says "Yes" → sends

**2:15 — Demo 3: Smart Interrupt (45s)**
Say: "Hey Suvi, delete the folder named old_projects on the desktop"
SUVI starts navigating to desktop, about to open folder
User says: "Wait, stop"
SUVI immediately stops. Widget shows "Stopped. The folder has not been touched."
This demonstrates interrupt capability — judges WANT to see this.

**3:00 — Architecture (45s)**
Show architecture diagram. "SUVI uses Gemini 2.5 Computer Use — Google's newest model, designed specifically for this use case. The orchestrator runs on Vertex AI Agent Engine, the gateway on Cloud Run, memory in Firestore."

**3:45 — Close (15s)**
"SUVI. Because the best interface is the one you already know how to use — your voice."
Show GCP console with real logs as final frame.

---

## CRITICAL REMINDERS FOR GEMINI CLI

When writing any code for this project:

1. **Always use `gemini-2.5-computer-use`** for the computer vision + action loop. This is the newest model and the key differentiator.

2. **Always use `qasync`** to bridge asyncio and PyQt6. Never block the Qt event loop with synchronous calls.

3. **Always emit `pyqtSignal`** when communicating from background threads/asyncio to the UI. Never call Qt methods from non-Qt threads.

4. **Always log to Cloud Logging** for every desktop action — this is submission proof.

5. **Firestore writes must be non-blocking** — use asyncio with the Firestore async client.

6. **The demo video is 30% of the score.** Every feature you build should have a clear 10-second demo moment.

7. **The architecture diagram is required.** Create `docs/architecture.png` on Day 4.

8. **PyInstaller build must work** — test `python -m PyInstaller suvi.spec` before Day 5.

9. **README spin-up must work on a fresh machine** — a judge will try to run it.

10. **Use `min_instances=1` on Cloud Run** — cold starts during the demo are disqualifying.
```
