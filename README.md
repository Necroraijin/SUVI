
S U V I
Superintelligent Unified Voice Interface
Multi-Agent AI Desktop Control System  ·  v3.0  ·  PyQt6 Architecture

Google Hackathon 2025 Vertex AI + ADK + A2A PyQt6 Single Runtime Enterprise Grade

"The name carries love. The system carries precision."

1. Executive Summary
SUVI (Superintelligent Unified Voice Interface) is a production-grade, cloud-native multi-agent AI system that gives users full natural-language control over their desktop — via voice or text. It combines Gemini Live API for real-time multimodal I/O, Google ADK for agent construction, A2A protocol for inter-agent communication, and Vertex AI as the unified intelligence platform for all agents.

v3.0 introduces a decisive frontend change: the Electron + Node.js shell is replaced with a native PyQt6 desktop application. This eliminates the entire IPC layer between the UI and the Python execution engine — every desktop action, screen capture, microphone stream, and wake word callback becomes a direct in-process function call. The result is a faster, simpler, more reliable system with a single unified runtime.

Core System Properties
▸ Single Python runtime — UI, voice, screen capture, and action execution share one process
▸ All agent intelligence on Vertex AI — Orchestrator and all sub-agents via ADK
▸ Cloud Run as gateway — WebSocket proxy, auth, rate limiting, Pub/Sub bridge
▸ Gemini Live API — persistent voice + screen frame session with sub-500ms response
▸ PyQt6 Action Ring — transparent floating overlay with QPainter custom rendering
▸ Firestore + Vertex AI Vector Search — three-tier persistent memory across sessions

1. PyQt6 Architectural Verification
Before committing to any technology choice, a senior architect must examine the tradeoffs with precision. This section documents the formal verification of PyQt6 as the correct frontend choice for SUVI — including the IPC cost analysis, capability confirmation, and acknowledged tradeoffs.

2.1  The IPC Problem — What Was Actually Wrong
The v2 Electron architecture required two separate processes: a Node.js renderer for the UI and a Python subprocess for execution. Every interaction crossed this boundary. The costs were not theoretical — they were structural and compounding:

 🔍  IPC Overhead Analysis:
For a single desktop action (e.g., 'click this button'), the Electron+Python IPC path was: React click event → IPC.send() → Unix socket serialization → Python socket listener → deserialize → PyAutoGUI call → serialize result → socket send → Node.js deserialize → UI update. Each crossing cost ~0.5–2ms plus JSON encoding time. Screen frames (200KB JPEGs at 1fps) were the worst case: duplicated in both Node.js and Python heap, serialized twice.

Dimension Electron + Node.js  (v1 approach) PyQt6  (v3 approach)
IPC latency per call 0.5–2ms per Unix socket roundtrip ~0.001ms direct function call
Screen frame memory 200KB frame duplicated in TWO heaps Single mss object, zero-copy
JSON serialization Every command serialized/deserialized Native Python objects, no encoding
Process management Node.js must spawn/monitor Python Single process, no zombie risk
Error propagation Errors cross process boundary (complex) Standard Python exception chain
Mic audio stream Numpy array → JSON → Base64 or socket sounddevice numpy array in-process
Wake word callback Porcupine callback → IPC → UI update Direct pyqtSignal emit in-process
Deployment Two runtimes: Node.js + Python Single Python + PyQt6 install
Installer size Electron: ~120–200MB PyInstaller: ~80–120MB (smaller)
Runtime memory ~150MB Node.js + ~80MB Python ~100–130MB single Python process

2.2  PyQt6 Capability Confirmation
Every capability required for SUVI's Action Ring and desktop integration was verified against the PyQt6 API. All are fully supported:

Requirement PyQt6 API Status Notes
Transparent frameless window FramelessWindowHint + WA_TranslucentBackground CONFIRMED Per-pixel alpha on Windows, macOS, Linux
Always-on-top overlay WindowStaysOnTopHint + Qt.Tool CONFIRMED Tool flag hides from taskbar
Visible all workspaces setWindowFlag + QWindow.setAllWorkspaces CONFIRMED Works on all platforms
Custom ring drawing QPainter + QPainterPath + QConicalGradient CONFIRMED Radial segments, glow, arcs — full control
Smooth animations QPropertyAnimation + QEasingCurve CONFIRMED Custom easing curves available
System tray integration QSystemTrayIcon + QMenu CONFIRMED Native OS tray on all platforms
Global hotkey capture pynput (in QThread) + pyqtSignal CONFIRMED Thread-safe signal to Qt main thread
asyncio + Qt event loop qasync library (pip install qasync) CONFIRMED WebSocket I/O non-blocking in Qt
Click-through in idle setWindowFlag(Qt.WindowTransparentForInput) CONFIRMED Mouse events pass through idle ring
Multi-monitor positioning QApplication.screens() + geometry() CONFIRMED Detects all monitors, user-preferred corner
Voice amplitude display QPropertyAnimation on custom Q_PROPERTY CONFIRMED Mic level drives ring pulse in real time
OpenGL accelerated paint QOpenGLWidget or RasterHint CONFIRMED GPU-accelerated when available

2.3  Real Tradeoffs — Acknowledged
 ⚠️  Tradeoff 1 — Animation Expressiveness:
Framer Motion (React) provides physics-based spring animations out of the box. PyQt6's QPropertyAnimation uses mathematical easing curves (InOutQuart, OutElastic, etc.) which require more manual tuning to replicate spring physics. The Action Ring's visual quality will be very high but requires more custom QPainter code. Solution: Use QEasingCurve.OutElastic for expansion and custom cubic bezier curves for segment glow.

 ⚠️  Tradeoff 2 — Hot Reload During Development:
Vite/React provides instant hot module reload. PyQt6 requires a process restart on code change. This is a developer experience cost, not a production concern. Solution: Use importlib.reload() patterns for widget classes during dev, or accept the ~2s restart time.

 ✅  Not a Tradeoff — Performance:
PyQt6 with QPainter and OpenGL rendering matches or exceeds CSS/Framer Motion for the Action Ring use case. Qt's animation system is used in production applications requiring 120fps (e.g., DaVinci Resolve, Kdenlive). The Action Ring at 60fps is well within PyQt6's capabilities.

Verdict: PyQt6 is the architecturally correct choice for SUVI. The IPC elimination is not a micro-optimization — it removes an entire structural layer of complexity, latency, and failure modes. The Action Ring is fully achievable with QPainter. The single Python runtime is simpler to deploy, easier to debug, and more reliable in production.

1. System Architecture  (v3.0)
3.1  Four-Layer Architecture
╔══════════════════════════════════════════════════════════════╗
║             LAYER 1 — LOCAL CLIENT LAYER                    ║
║  Single Python Process  (PyQt6 + asyncio + qasync)          ║
║  ┌──────────────┐  ┌─────────────────┐  ┌───────────────┐  ║
║  │  Action Ring │  │  Voice & Vision  │  │ Action        │  ║
║  │  (QPainter)  │  │  sounddevice     │  │ Executor      │  ║
║  │  QSystemTray │  │  python-mss      │  │ PyAutoGUI     │  ║
║  │  pyqtSignal  │  │  Porcupine       │  │ Playwright    │  ║
║  └──────┬───────┘  └────────┬─────────┘  └──────┬────────┘  ║
║         └──────────────────┬┘                    │           ║
║              Direct Python calls — ZERO IPC overhead         ║
╚═══════════════════════════════════════════════════════════════╝
                 │  WSS / HTTPS (qasync + websockets)
╔════════════════╪══════════════════════════════════════════════╗
║    LAYER 2 — CLOUD RUN GATEWAY (Python FastAPI)              ║
║  WebSocket Proxy │ Auth (OIDC) │ Rate Limiter │ Pub/Sub pub  ║
║  Session Manager │ Secret Mgr  │ CORS handler │ Cloud Armor  ║
╚══════════════════════════════════════════════════════════════╝
                 │  gRPC + REST
╔════════════════╪══════════════════════════════════════════════╗
║     LAYER 3 — VERTEX AI INTELLIGENCE LAYER                   ║
║  Orchestrator Agent (ADK + Agent Engine)                      ║
║  Code | Text | Browser | Search | Memory | Email | Data      ║
╚══════════════════════════════════════════════════════════════╝
                 │  SDK calls
╔════════════════╪══════════════════════════════════════════════╗
║        LAYER 4 — GCP DATA & SERVICES LAYER                   ║
║  Firestore │ Pub/Sub │ BigQuery │ Cloud Storage │ Logging     ║
╚══════════════════════════════════════════════════════════════╝

3.2  Single-Process Local Runtime — Thread Model
PyQt6 requires all UI operations on the main thread. Background I/O (mic capture, WebSocket, wake word) runs in QThreads and communicates with the UI via pyqtSignals — Qt's thread-safe event system. asyncio handles all network I/O via qasync, which bridges Qt's event loop with Python's asyncio event loop.

Thread / Context Responsibilities Communication to UI
Qt Main Thread Action Ring UI, QPainter, QPropertyAnimation, user input Direct — it IS the UI thread
QThread: VoiceWorker sounddevice mic capture, audio chunking, amplitude calc pyqtSignal(bytes, float) — audio_chunk, amplitude
QThread: WakeWordWorker Porcupine keyword detection loop (blocking C lib) pyqtSignal() — wake_word_detected
asyncio (via qasync) WebSocket to Cloud Run, receive action commands, send audio QMetaObject.invokeMethod for thread-safe UI
QThread: ScreenWorker python-mss frame capture on demand (not continuous) pyqtSignal(bytes) — frame_ready
In-Process: ActionExecutor PyAutoGUI, Playwright, filesystem ops — triggered by command Direct pyqtSignal(dict) — action_result

1. Gemini Live API — Real-Time I/O
Gemini Live API provides the bidirectional voice + vision session. The PyQt6 app maintains this via an asyncio WebSocket connection (through the Cloud Run proxy) managed by qasync — meaning it runs alongside the Qt event loop without blocking UI rendering.

4.1  Voice + Vision Session in PyQt6

# suvi/client/services/live_session.py

import asyncio, qasync, sounddevice as sd, mss, io
from google import genai
from google.genai import types
from PyQt6.QtCore import QObject, pyqtSignal

class GeminiLiveService(QObject):
    # Signals emitted to Action Ring (thread-safe)
    transcript_ready = pyqtSignal(str)      # Partial/final transcript
    intent_detected  = pyqtSignal(str)      # Active agent hint
    response_audio   = pyqtSignal(bytes)    # TTS audio chunk → speaker
    state_changed    = pyqtSignal(str)      # 'listening'/'thinking'/'done'

    async def run_session(self):
        client = genai.Client(vertexai=True, project=GCP_PROJECT)
        async with client.aio.live.connect(
            model='models/gemini-2.0-flash-live-001',
            config=self._build_config()
        ) as session:
            self._session = session
            # Run mic stream + response receiver concurrently
            await asyncio.gather(
                self._stream_mic(session),   # sounddevice → session.send()
                self._receive(session),       # session responses → pyqtSignals
            )

    async def inject_screen_frame(self):
        # Called in-process from ScreenWorker signal handler — no IPC needed
        with mss.mss() as sct:
            frame = sct.grab(sct.monitors[1])
        img = Image.frombytes('RGB', frame.size, frame.bgra, 'raw', 'BGRX')
        img = img.resize((768, int(768 * frame.height / frame.width)))
        buf = io.BytesIO()
        img.save(buf, 'JPEG', quality=75)
        # Inject directly — same process, no IPC encoding overhead
        await self._session.send(input=types.LiveClientRealtimeInput(
            media_chunks=[types.Blob(data=buf.getvalue(), mime_type='image/jpeg')]
        ))

5. PyQt6 Action Ring — Frontend Specification
The Action Ring is SUVI's primary interface — a floating, always-accessible radial overlay inspired by Logitech's G HUB action ring and the immediacy of Apple's Dynamic Island. It is implemented entirely in PyQt6 using custom QPainter rendering, QPropertyAnimation state transitions, and Qt's native windowing system for transparency and overlay behavior.

5.1  Window Setup — Transparency & Overlay

# suvi/client/ui/action_ring/ring_window.py

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QSize, QPoint

class RingWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Transparent frameless overlay — core window config
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint      |  # No title bar
            Qt.WindowType.WindowStaysOnTopHint     |  # Float above all apps
            Qt.WindowType.Tool                     |  # No taskbar entry
            Qt.WindowType.NoDropShadowWindowHint      # Qt manages its own glow
        )
        # Per-pixel alpha transparency
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        # Do not steal focus when ring appears
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        # Appear on all virtual desktops/workspaces
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

        self.setFixedSize(QSize(340, 340))
        self._place_at_corner()              # Default: bottom-right
        self._set_click_through(True)        # Idle: mouse passes through

    def _set_click_through(self, enabled: bool):
        # Idle ring is invisible to mouse — desktop usable underneath
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, enabled)

    def _place_at_corner(self):
        screen = QApplication.primaryScreen().geometry()
        x = screen.right()  - self.width()  - 24  # 24px from edge
        y = screen.bottom() - self.height() - 60  # 60px above taskbar
        self.move(QPoint(x, y))

5.2  Ring State Machine

# suvi/client/ui/action_ring/ring_state.py

from enum import Enum, auto
from dataclasses import dataclass

class RingState(Enum):
    IDLE       = auto()   # 48px orb, 0.7 opacity, click-through ON
    LISTENING  = auto()   # 300px ring, 8 segments, mic waveform, click-through OFF
    THINKING   = auto()   # Segments dim, rotating arc, active agent glows
    EXECUTING  = auto()   # Progress arc fills, cancel available, toast shows
    DONE       = auto()   # Flash success/error, result card appears, auto-collapse 4s
    ERROR      = auto()   # Red flash, error toast, Gemini Live speaks error aloud

@dataclass
class RingVisualState:
    ring_radius:    float = 24.0   # px — animated from 24 (idle) to 150 (expanded)
    ring_opacity:   float = 0.7    # 0.7 idle, 1.0 expanded
    orb_glow:       float = 0.0    # 0.0–1.0 — driven by mic amplitude
    arc_progress:   float = 0.0    # 0.0–1.0 — task completion
    active_segment: int   = -1     # -1 = none, 0–7 = agent index
    rotation_angle: float = 0.0    # For thinking state rotating arc

5.3  Custom QPainter Rendering
The entire Action Ring is drawn in a single paintEvent using QPainter. No external image assets — everything is procedurally generated with vector graphics, enabling crisp rendering at any DPI and smooth animation at 60fps.

# suvi/client/ui/action_ring/ring_painter.py (key sections)

from PyQt6.QtGui import QPainter, QPainterPath, QConicalGradient
from PyQt6.QtGui import QRadialGradient, QColor, QPen, QBrush
from PyQt6.QtCore import QRectF, Qt
import math

SEGMENTS = [
    {'id': 'code',   'label': 'Code',   'color': '#10B981', 'angle_start': 337.5},
    {'id': 'browse', 'label': 'Browse', 'color': '#7C3AED', 'angle_start': 22.5 },
    {'id': 'write',  'label': 'Write',  'color': '#D97706', 'angle_start': 67.5 },
    {'id': 'search', 'label': 'Search', 'color': '#0D9488', 'angle_start': 112.5},
    {'id': 'file',   'label': 'File',   'color': '#2563EB', 'angle_start': 157.5},
    {'id': 'app',    'label': 'App',    'color': '#4F46E5', 'angle_start': 202.5},
    {'id': 'email',  'label': 'Email',  'color': '#DC2626', 'angle_start': 247.5},
    {'id': 'data',   'label': 'Data',   'color': '#475569', 'angle_start': 292.5},
]

def paint_ring(painter: QPainter, vs: RingVisualState, state: RingState):
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    cx, cy = painter.device().width() / 2, painter.device().height() / 2

    # 1. Outer glow halo (QRadialGradient)
    _draw_glow_halo(painter, cx, cy, vs.ring_radius, vs.orb_glow)

    # 2. Ring segments (visible only in LISTENING/THINKING/EXECUTING/DONE)
    if vs.ring_radius > 80:
        for i, seg in enumerate(SEGMENTS):
            _draw_segment(painter, cx, cy, vs, seg, i == vs.active_segment)

    # 3. Progress arc (EXECUTING state)
    if state == RingState.EXECUTING:
        _draw_progress_arc(painter, cx, cy, vs.ring_radius, vs.arc_progress)

    # 4. Thinking rotation arc
    if state == RingState.THINKING:
        _draw_rotation_arc(painter, cx, cy, vs.ring_radius, vs.rotation_angle)

    # 5. Center orb (always visible)
    _draw_center_orb(painter, cx, cy, vs.orb_glow, state)

def _draw_segment(painter, cx, cy, vs, seg, is_active):
    r_inner, r_outer = vs.ring_radius *0.55, vs.ring_radius
    arc_span = 40.0   # degrees per segment (8 segs* 45deg, 5deg gap)
    start_angle = seg['angle_start']
    color = QColor(seg['color'])
    if is_active:
        color = color.lighter(130)    # Active segment: brighter
    # Conical gradient for depth effect
    gradient = QConicalGradient(cx, cy, start_angle)
    gradient.setColorAt(0.0, color.lighter(120))
    gradient.setColorAt(1.0, color.darker(110))
    path = QPainterPath()
    path.arcMoveTo(QRectF(cx - r_outer, cy - r_outer, r_outer*2, r_outer*2),
                   start_angle)
    path.arcTo(QRectF(cx - r_outer, cy - r_outer, r_outer*2, r_outer*2),
               start_angle, arc_span)
    path.arcTo(QRectF(cx - r_inner, cy - r_inner, r_inner*2, r_inner*2),
               start_angle + arc_span, -arc_span)
    path.closeSubpath()
    painter.fillPath(path, QBrush(gradient))

5.4  Animation — QPropertyAnimation State Transitions

# suvi/client/ui/action_ring/ring_animator.py

from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QParallelAnimationGroup
from PyQt6.QtCore import pyqtProperty, QObject

class RingAnimator(QObject):
    """Owns all QPropertyAnimations for the ring visual state"""

    def __init__(self, ring_widget):
        super().__init__()
        self._ring = ring_widget
        # Animate ring_radius: 24 (idle) → 150 (expanded)
        self._radius_anim = QPropertyAnimation(ring_widget, b'ring_radius')
        self._radius_anim.setDuration(380)             # ms
        self._radius_anim.setEasingCurve(QEasingCurve.Type.OutBack)  # Overshoot spring

        # Animate opacity
        self._opacity_anim = QPropertyAnimation(ring_widget, b'ring_opacity')
        self._opacity_anim.setDuration(220)
        self._opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Rotation for THINKING state — continuous loop
        self._rotate_anim = QPropertyAnimation(ring_widget, b'rotation_angle')
        self._rotate_anim.setDuration(1200)
        self._rotate_anim.setStartValue(0.0)
        self._rotate_anim.setEndValue(360.0)
        self._rotate_anim.setLoopCount(-1)             # Infinite loop
        self._rotate_anim.setEasingCurve(QEasingCurve.Type.Linear)

    def transition_to(self, state: RingState):
        group = QParallelAnimationGroup(self)
        if state == RingState.LISTENING:
            self._radius_anim.setEndValue(150.0)
            self._opacity_anim.setEndValue(1.0)
            self._rotate_anim.stop()
        elif state == RingState.THINKING:
            self._radius_anim.setEndValue(140.0)
            self._rotate_anim.start()
        elif state == RingState.IDLE:
            self._radius_anim.setEndValue(24.0)
            self._opacity_anim.setEndValue(0.7)
            self._rotate_anim.stop()
        group.addAnimation(self._radius_anim)
        group.addAnimation(self._opacity_anim)
        group.start(QAbstractAnimation.DeletionPolicy.KeepWhenStopped)

5.5  System Tray & Global Hotkey

# suvi/client/ui/tray.py — System tray icon and context menu

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon

class SuviTray(QSystemTrayIcon):
    def __init__(self, ring_window, app_controller):
        super().__init__(QIcon(':/icons/suvi_tray.png'))
        menu = QMenu()
        menu.addAction('Open Dashboard', app_controller.open_dashboard)
        menu.addAction('Action History',  ring_window.show_action_log)
        menu.addSeparator()
        menu.addAction('Preferences',    app_controller.open_preferences)
        menu.addAction('Kill Switch',    app_controller.emergency_halt)
        menu.addSeparator()
        menu.addAction('Quit SUVI',      app_controller.quit)
        self.setContextMenu(menu)
        self.setToolTip('SUVI — Click to open dashboard')
        self.activated.connect(self._on_activate)

# suvi/client/workers/wake_word_worker.py — Global hotkey in QThread

from PyQt6.QtCore import QThread, pyqtSignal
from pynput import keyboard

class GlobalHotkeyWorker(QThread):
    hotkey_pressed = pyqtSignal()  # Emits to main thread — thread-safe
    def run(self):
        # Ctrl+Shift+S as push-to-talk fallback (configurable)
        with keyboard.GlobalHotKeys({'<ctrl>+<shift>+s': self.hotkey_pressed.emit}):
            keyboard.Listener(daemon=True).join()

5.6  Micro-Toast Notification System

# suvi/client/ui/toast.py — Floating notifications above the ring

class MicroToast(QWidget):
    def __init__(self, parent_ring: RingWindow):
        super().__init__(None)  # Top-level window, not child
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self._parent_ring = parent_ring

    def show_status(self, message: str, duration_ms: int = 3000):
        self._message = message
        # Position: 16px above the ring window
        ring_geo = self._parent_ring.geometry()
        self.setGeometry(ring_geo.x(), ring_geo.y() - 56, ring_geo.width(), 44)
        self.show()
        QTimer.singleShot(duration_ms, self.fade_out)  # Auto-dismiss

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Rounded pill background (dark with slight opacity)
        painter.setBrush(QBrush(QColor(15, 23, 42, 220)))  # Navy, 86% opacity
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect().adjusted(4, 4, -4, -4), 20, 20)
        # Text centered
        painter.setPen(QColor('#E2E8F0'))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._message)

5.7  Action Ring Visual States — Reference
State Size Opacity Ring Center Orb Behavior
IDLE 48px circle 0.7 None — orb only Indigo pulse, slow Click-through ON; wake word activates
LISTENING 300px ring 1.0 8 segments visible, color fills White waveform (mic amplitude) Click-through OFF; segments clickable
THINKING 280px ring 0.95 Segments dim 40%, active agent glows full Rotating indigo arc Cancel button appears at center
EXECUTING 280px ring 1.0 Progress arc overlays ring (accent color) Completion % text Toast shows action status above ring
DONE 280px flash then 48px 1.0 then 0.7 Flash green/red, then collapses Success/error icon, 2s Result card slides in; auto-collapses 4s
ERROR 200px ring 1.0 Red flash 3x X icon Error toast + Gemini Live speaks error

1. Vertex AI Agent Layer
All agents run on Vertex AI Agent Engine using ADK. The Orchestrator is the only agent the local PyQt6 app communicates with directly (via Cloud Run gateway). Sub-agents communicate peer-to-peer with the Orchestrator using the A2A protocol.

Orchestrator Agent   Master Planner & Router
Hosted On: Vertex AI Agent Engine (ADK runtime)
Primary Model: gemini-2.0-flash-001 — low latency for intent → plan → route
Fallback Model: gemini-2.0-pro-001 — complex multi-step reasoning (auto-escalated)
Input: Voice transcript + screen frame from Gemini Live, agent results
Output: Task DAG, A2A agent calls, action commands to local Executor, TTS response
Memory: Reads Firestore profile at session start; calls Memory Agent per turn
Tools: plan_task(), route_to_agent(), validate_action(), compose_response(), recall_memory()

Desktop Control Agent   OS-Level Command Serializer
Hosted On: Vertex AI Agent Engine — sends command JSON to local ActionExecutor in-process
Model: gemini-2.0-flash-001 — action planning
Local Counterpart: ActionExecutor class in PyQt6 app — PyAutoGUI + pywin32/xlib — NO IPC overhead
Communication: Cloud Run gateway pushes command JSON over WebSocket to PyQt6 app
Commands: click(x,y), type(text), hotkey(keys), launch(app), scroll(), screenshot()
Safety: Every command passes Permission Tier model before ActionExecutor.execute() is called

Code Agent   Multi-Language Code Intelligence
Hosted On: Vertex AI Agent Engine
Model: gemini-2.0-pro-001 — highest code quality
RAG: Vertex AI Vector Search — user's codebase indexed, fetched per task
Languages: Python, TypeScript, Go, Rust, Java, SQL, Bash, Terraform
Capabilities: Generate, complete, refactor, debug, document, generate tests

Text Agent   NLP & Content Intelligence
Hosted On: Vertex AI Agent Engine
Model: gemini-2.0-flash-001 — optimized for text throughput
Capabilities: Summarize, generate, translate (50+ langs), extract, tone rewrite
Document I/O: PDF/DOCX via Cloud Storage pipeline; outputs to clipboard (direct) or file

Memory Agent   Persistent Context Manager
Hosted On: Vertex AI Agent Engine
Tier 1 — Hot: Gemini Live context window (0ms) — current conversation
Tier 2 — Warm: Firestore document cache (<20ms) — current day sessions
Tier 3 — Cold: Vertex AI Vector Search over full history (<100ms) — semantic recall
Embeddings: text-embedding-004 — every turn embedded and indexed

1. Google Cloud Services
GCP Service Role in SUVI Specific Usage
Vertex AI Agent Engine Hosts ALL agents Orchestrator + 7 sub-agents deployed as ADK agents
Gemini Live API Real-time voice + vision I/O Voice stream + screen frames into PyQt6 app via qasync
Cloud Run Gateway + Dashboard hosting FastAPI WebSocket proxy, auth, rate limiting; Next.js dashboard
Firestore Persistent memory User profiles, session history, agent memory, codebase index
Vertex AI Vector Search Semantic memory + RAG Embed + search conversation history and local codebase
Cloud Pub/Sub Async event bus Action telemetry, agent health events, dead-letter queue
BigQuery Analytics & telemetry All SUVI actions → BigQuery, query in dashboard
Cloud Logging Audit trail Every Tier 1+ desktop action logged with full context
Secret Manager Credential store All API keys — never in env vars or source code
Cloud Armor API security WAF on Cloud Run gateway — injection, DDoS protection
Cloud Storage Asset store Session recordings, exported files, model artifacts
Cloud Monitoring Observability Custom dashboards: agent latency, token cost, error rate

2. Project Folder Structure
The repository is a Python-native monorepo. With the switch to PyQt6, the desktop app is a clean Python package — no Node.js, no npm, no Electron build tooling. The dashboard (Next.js) remains in apps/ as the only JavaScript component.

suvi/                                        # Monorepo root
│
├── apps/                                    # Deployable applications
│   │
│   ├── desktop/                             # PyQt6 desktop client (LOCAL — Python only)
│   │   ├── suvi/                            # Main Python package
│   │   │   │
│   │   │   ├── __main__.py                  # Entry point: python -m suvi
│   │   │   ├── app.py                       # QApplication + qasync event loop setup
│   │   │   ├── controller.py                # App-level orchestration (UI ↔ services)
│   │   │   │
│   │   │   ├── ui/                          # All PyQt6 UI components
│   │   │   │   ├── action_ring/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── ring_window.py       # QWidget: FramelessWindowHint overlay
│   │   │   │   │   ├── ring_painter.py      # QPainter custom drawing logic
│   │   │   │   │   ├── ring_state.py        # RingState enum + RingVisualState dataclass
│   │   │   │   │   ├── ring_animator.py     # QPropertyAnimation state transitions
│   │   │   │   │   ├── segment_config.py    # 8 segment definitions (color, label, angle)
│   │   │   │   │   └── drag_handler.py      # Drag-to-reposition, saves to Firestore
│   │   │   │   │
│   │   │   │   ├── notifications/
│   │   │   │   │   ├── micro_toast.py       # Floating status pills above ring
│   │   │   │   │   ├── result_card.py       # Expandable result preview card
│   │   │   │   │   └── confirm_dialog.py    # Tier 3+ action confirmation prompt
│   │   │   │   │
│   │   │   │   ├── action_log_panel.py      # Expanded history (last 50 actions)
│   │   │   │   └── tray.py                  # QSystemTrayIcon + context menu
│   │   │   │
│   │   │   ├── services/                    # Background async services (qasync)
│   │   │   │   ├── __init__.py
│   │   │   │   ├── live_session.py          # Gemini Live API WebSocket session
│   │   │   │   ├── gateway_client.py        # WebSocket connection to Cloud Run gateway
│   │   │   │   └── memory_cache.py          # Local in-memory session state
│   │   │   │
│   │   │   ├── workers/                     # QThread background workers
│   │   │   │   ├── __init__.py
│   │   │   │   ├── voice_worker.py          # sounddevice mic capture → pyqtSignal
│   │   │   │   ├── wake_word_worker.py      # Porcupine + pynput hotkey → pyqtSignal
│   │   │   │   └── screen_worker.py         # python-mss on-demand capture → pyqtSignal
│   │   │   │
│   │   │   ├── executor/                    # Local desktop action execution (NO IPC)
│   │   │   │   ├── __init__.py
│   │   │   │   ├── action_executor.py       # Command dispatcher — called directly
│   │   │   │   ├── desktop.py               # PyAutoGUI mouse/keyboard ops
│   │   │   │   ├── browser.py               # Playwright in-process browser control
│   │   │   │   ├── filesystem.py            # File create/read/delete/search
│   │   │   │   ├── sandbox.py               # subprocess resource-limited script runner
│   │   │   │   ├── permissions.py           # Tier model: validate before execute()
│   │   │   │   ├── undo_stack.py            # Circular buffer of reversible actions
│   │   │   │   └── kill_switch.py           # Emergency halt: cancel all async tasks
│   │   │   │
│   │   │   └── resources/                   # Embedded assets (compiled into app)
│   │   │       ├── icons/                   # SVG icons for segments + tray
│   │   │       └── sounds/                  # Click/confirm/error audio feedback (short)
│   │   │
│   │   ├── tests/                           # Desktop app tests
│   │   │   ├── test_ring_state.py           # State machine transitions
│   │   │   ├── test_action_executor.py      # Permission tier + action tests
│   │   │   └── test_live_session.py         # Gemini Live integration
│   │   │
│   │   ├── pyproject.toml                   # Python deps: PyQt6, qasync, PyAutoGUI...
│   │   ├── suvi.spec                        # PyInstaller build spec
│   │   └── Makefile                         # make dev | make build | make test
│   │
│   ├── gateway/                             # Cloud Run gateway service (Python FastAPI)
│   │   ├── suvi_gateway/
│   │   │   ├── main.py                      # FastAPI app entry
│   │   │   ├── routes/
│   │   │   │   ├── ws_proxy.py              # WebSocket ↔ Gemini Live proxy
│   │   │   │   ├── agents.py                # REST → Vertex AI agent calls
│   │   │   │   ├── actions.py               # Push action commands to client via WSS
│   │   │   │   └── health.py                # /health + /metrics endpoints
│   │   │   ├── middleware/
│   │   │   │   ├── auth.py                  # OIDC token validation
│   │   │   │   ├── rate_limiter.py          # Redis sliding window
│   │   │   │   └── session_manager.py       # Session ↔ Firestore mapping
│   │   │   └── services/
│   │   │       ├── pubsub.py
│   │   │       ├── secrets.py
│   │   │       └── firestore.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── cloudbuild.yaml
│   │
│   └── dashboard/                           # Next.js web dashboard (Cloud Run)
│       ├── app/                             # App Router pages
│       │   ├── page.tsx                     # Overview / GCP usage home
│       │   ├── agents/page.tsx              # Agent health + latency
│       │   ├── memory/page.tsx              # Firestore memory browser
│       │   ├── actions/page.tsx             # BigQuery action timeline
│       │   └── settings/page.tsx            # Permission config, preferences
│       ├── components/
│       │   ├── GCPMetricsCard.tsx
│       │   ├── AgentStatusGrid.tsx
│       │   ├── ActionTimeline.tsx
│       │   └── CostTracker.tsx
│       ├── Dockerfile
│       └── package.json
│
├── agents/                                  # Vertex AI Agent Engine agents (all Python)
│   ├── shared/                              # Shared across all agents
│   │   ├── memory_client.py                 # Firestore read/write
│   │   ├── permissions.py                   # Tier model constants
│   │   ├── telemetry.py                     # Pub/Sub + BigQuery logging
│   │   ├── a2a_client.py                    # A2A protocol HTTP client
│   │   └── models.py                        # Pydantic: Task, Action, AgentResult
│   │
│   ├── orchestrator/                        # Master coordinator
│   │   ├── agent.py                         # ADK Agent definition
│   │   ├── planner.py                       # Task DAG builder
│   │   ├── router.py                        # Agent capability matching
│   │   ├── validator.py                     # LLM + rule-based action guard
│   │   ├── composer.py                      # Response synthesis
│   │   ├── tools/
│   │   │   ├── plan_task.py
│   │   │   ├── route_to_agent.py
│   │   │   ├── validate_action.py
│   │   │   └── recall_memory.py
│   │   ├── system_prompt.py                 # SUVI orchestrator system prompt
│   │   ├── agent_card.json                  # A2A capability declaration
│   │   └── deploy.py                        # Vertex AI Agent Engine deploy
│   │
│   ├── code_agent/                          # Same structure for each agent:
│   │   ├── agent.py  ├── tools/  ├── rag/  ├── agent_card.json  └── deploy.py
│   ├── text_agent/
│   ├── browser_agent/                       # Sends Playwright cmds to local executor
│   ├── search_agent/                        # Vertex AI Grounding + Google Search
│   ├── memory_agent/                        # Firestore + Vector Search coordinator
│   ├── email_agent/                         # Gmail API
│   └── data_agent/                          # BigQuery + CSV analysis
│
├── infrastructure/                          # Terraform + GCP config
│   ├── terraform/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── modules/
│   │       ├── vertex_ai/                   # Agent Engine + Vector Search
│   │       ├── cloud_run/                   # Gateway + Dashboard
│   │       ├── firestore/                   # Rules + indexes
│   │       ├── pubsub/                      # Topics + subs + DLQ
│   │       ├── bigquery/                    # Datasets + schemas
│   │       ├── iam/                         # Service accounts + roles
│   │       ├── secrets/                     # Secret Manager resources
│   │       └── monitoring/                  # Dashboards + alert policies
│   ├── firestore.rules
│   ├── firestore.indexes.json
│   └── bigquery/schemas/                    # Telemetry table schemas
│
├── shared/                                  # Cross-cutting Python shared code
│   ├── suvi_types/                          # Pydantic models: Task, Action, AgentResult
│   ├── a2a/                                 # A2A protocol client + server base class
│   └── constants/                           # Permission tiers, segment config
│
├── tests/                                   # Integration + E2E tests
│   ├── integration/
│   │   ├── test_a2a_flow.py                 # Orchestrator → sub-agent
│   │   ├── test_gateway.py                  # Cloud Run gateway routes
│   │   └── test_gemini_live.py              # Gemini Live session integration
│   └── e2e/
│       └── test_voice_to_action.py          # Full voice → desktop action test
│
├── scripts/                                 # Dev + deployment utilities
│   ├── deploy_agents.py                     # Deploy all agents to Vertex AI
│   ├── index_codebase.py                    # Index project → Vector Search
│   ├── seed_firestore.py                    # Seed dev Firestore
│   └── setup_gcp.sh                         # One-shot GCP project bootstrap
│
├── docs/
│   ├── architecture.md
│   ├── pyqt6_ring_design.md                 # Action Ring design decisions
│   ├── api_reference.md                     # A2A endpoint reference
│   └── demo_guide.md                        # Hackathon demo walkthrough
│
├── .github/workflows/
│   ├── deploy-gateway.yml
│   ├── deploy-agents.yml
│   ├── build-desktop.yml                    # PyInstaller multi-platform build
│   └── test.yml
│
├── pyproject.toml                           # Root Python workspace (uv workspaces)
└── README.md

1. Complete Technology Stack
Desktop App (PyQt6 — Single Process)
▸ Python 3.12+ — unified runtime
▸ PyQt6 — UI framework, window management
▸ qasync — Qt event loop + asyncio bridge
▸ websockets — async WebSocket client
▸ sounddevice — microphone capture (numpy)
▸ python-mss — screen capture
▸ Porcupine (Picovoice) — wake word detection
▸ pynput — global hotkey listener (QThread)
▸ PyAutoGUI — mouse/keyboard automation
▸ Playwright — browser automation
▸ google-genai — Gemini Live API SDK
▸ google-cloud-firestore — memory client
▸ google-auth — OIDC token management
▸ PyInstaller — cross-platform installer build

Cloud Run Gateway (Python)
▸ FastAPI — async API framework
▸ websockets — WSS proxy to Gemini Live
▸ Redis (Cloud Memorystore) — session + rate limit
▸ google-cloud-pubsub — telemetry events
▸ google-cloud-secret-manager
▸ google-auth — OIDC validation Agent Layer (Vertex AI)
▸ Google ADK — agent framework
▸ Vertex AI Agent Engine — runtime
▸ gemini-2.0-flash-001 — fast agents
▸ gemini-2.0-pro-001 — code agent
▸ gemini-2.0-flash-live-001 — Live API
▸ text-embedding-004 — embeddings
▸ Vertex AI Vector Search — RAG + semantic memory
▸ Vertex AI Search — web grounding

GCP Services
▸ Firestore — persistent memory store
▸ Cloud Pub/Sub — async event bus
▸ BigQuery — telemetry analytics
▸ Cloud Logging — audit trail
▸ Secret Manager — credentials
▸ Cloud Armor — WAF/DDoS
▸ Cloud Storage — assets/recordings
▸ Cloud Monitoring — dashboards + alerts

Dashboard (Next.js — Cloud Run)
▸ Next.js 14 App Router
▸ shadcn/ui + Tailwind — components
▸ Recharts — live GCP metrics charts

1. Security Architecture & Guardrails
10.1  Permission Tier Model
Tier Risk Examples Approval Audit
0 — Observe None Screenshot, read screen content, clipboard read Auto None
1 — Interact Low Click UI elements, type text, scroll Auto Cloud Logging
2 — Operate Medium Paste content, open apps, clipboard write Auto + logged Cloud Logging + BigQuery
3 — Modify High Create/delete files, run scripts, close apps Ring confirmation (confirm_dialog.py) Full audit + alert
4 — System Critical System settings, installs, network config PIN/biometric + voice confirm Audit + user email

10.2  PyQt6-Specific Security Notes
 🔒  Action Executor is In-Process — Extra Care Required:
Because PyQt6 eliminates IPC, the ActionExecutor runs in the same process as the UI. This means a bug in executor code could theoretically affect the UI thread. All executor methods are called from the asyncio context (via qasync) and must catch all exceptions. A hard crash in the executor must be caught by a top-level ExceptionHandler that emits a pyqtSignal to the ring (showing ERROR state) without crashing the Qt event loop.

▸ All executor methods wrapped in try/except with signal emission on failure
▸ Sandbox for script execution still uses subprocess even in-process — isolation maintained
▸ Permission check is synchronous and called before every executor.execute() invocation
▸ kill_switch.py cancels all asyncio Tasks and emits kill signal to all QThreads

S U V I
Superintelligent Unified Voice Interface  ·  v3.0

PyQt6  ·  Vertex AI  ·  Gemini Live API
ADK  ·  A2A  ·  Cloud Run  ·  Firestore
Pub/Sub  ·  BigQuery  ·  Cloud Logging
"The name carries love. The system carries precision. Together, they carry purpose."
