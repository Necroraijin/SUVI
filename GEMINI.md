# SUVI Project Mandates & Task Tracker (Gemini CLI)

## 🎯 Project Context: Gemini Live Agent Challenge 2025

You are building **SUVI (Superintelligent Unified Voice Interface)**, a production-grade AI agent that controls a user's desktop using natural voice and text.

- **Goal:** Win the Gemini Live Agent Challenge (Categories: UI Navigator + Live Agents).
- **Core Differentiator:** Use `gemini-2.5-computer-use` to interpret the screen and execute actions without DOM/API access.

## ⚠️ Critical Engineering Directives (NEVER IGNORE)

1. **NO STUBS:** Always write complete, runnable, production-ready code. Never leave placeholders like `pass` or `TODO` unless explicitly asked.
2. **MODEL IDS:** Strictly use these exact Google model IDs:
   - Vision/Action: `gemini-2.5-computer-use-preview-10-2025`
   - Voice I/O: `gemini-2.0-flash-live-001`
   - Orchestrator: `gemini-2.5-pro-preview-06-05`
3. **UI CONCURRENCY:** The desktop app uses `PyQt6` and `qasync`. **Never** block the Qt event loop. **Always** use `pyqtSignal` to communicate from background threads/asyncio to the UI.
4. **NO IPC:** Keep the desktop client as a single Python process. No Node.js, no Electron.
5. **AUDIT TRAIL:** Every desktop action must log to Cloud Logging for hackathon proof.
6. **INTERRUPTIBILITY:** The system must be able to stop mid-task when the user says "stop".

## 🏗️ Architecture Layers

1. **Local (PyQt6):** Chat widget UI, Mic capture (`sounddevice`), Screen capture (`python-mss`), Action execution (`pyautogui`, `playwright`).
2. **Gateway (Cloud Run):** FastAPI WebSocket proxy, Firebase Auth, Rate limiting.
3. **Agent (Vertex AI):** Google ADK agent ("SUVI Orchestrator") managing tools.
4. **Data (GCP):** Firestore (memory), Pub/Sub & BigQuery (telemetry), Cloud Logging.

## 📋 5-Day Build Plan & Task Tracker

### Day 1 — Foundation (Computer Use Loop)

- [ ] Set up GCP project (`setup_gcp.sh`).
- [ ] `apps/desktop/suvi/__main__.py` & `app.py` (PyQt6 + qasync skeleton).
- [ ] `apps/desktop/suvi/services/computer_use_service.py` (Gemini 2.5 API calls).
- [ ] `apps/desktop/suvi/executor/` (PyAutoGUI dispatcher).
- [ ] `apps/desktop/suvi/workers/screen_worker.py` (mss capture).
- [ ] Test loop: Hardcoded intent -> Screenshot -> Gemini -> PyAutoGUI action.

### Day 2 — Voice + Memory

- [ ] `apps/desktop/suvi/services/live_session.py` (Gemini Live WebSocket).
- [ ] `apps/desktop/suvi/workers/voice_worker.py` (sounddevice mic capture).
- [ ] Firebase Auth integration.
- [ ] `apps/desktop/suvi/services/memory_service.py` (Firestore).
- [ ] Test full loop: Voice command -> Action execution with memory context.

### Day 3 — Cloud Infrastructure + Gateway

- [ ] `apps/gateway/` FastAPI Cloud Run service implementation.
- [ ] Deploy Gateway to Cloud Run.
- [ ] `agents/orchestrator/` ADK agent implementation.
- [ ] Deploy Orchestrator to Vertex AI Agent Engine.
- [ ] Wire Local App -> Gateway -> Vertex AI.

### Day 4 — UI Polish + Features

- [ ] `apps/desktop/suvi/ui/login/` (Login window).
- [ ] `apps/desktop/suvi/ui/widget/` (Floating chat widget, animations).
- [ ] Implement Smart Interrupt feature.
- [ ] Implement SUVI Replay feature (GIF recording).
- [ ] Implement Autopilot Mode.

### Day 5 — Demo + Submission Prep

- [ ] Record 4-minute demo video.
- [ ] Create Architecture diagram (`docs/architecture.png`).
- [ ] Finalize README with spin-up instructions.
- [ ] Verify GCP proof logs.
- [ ] Devpost submission.
