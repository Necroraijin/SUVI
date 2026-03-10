# SUVI Project Mandates & Task Tracker (Gemini CLI)

## 🎯 Project Context & Vision: Gemini Live Agent Challenge 2025

**SUVI (Superintelligent Unified Voice Interface)** is more than a technical solution; it is a deeply personal mission. Named in tribute to a loved one, SUVI carries forward a legacy of support, guidance, and care into the digital age.

### 🕊️ The Story & The Why
This project was born from the desire to bridge the gap between human intent and machine execution for those who face the greatest barriers. We believe that technology should be an equalizer, not another obstacle. SUVI is dedicated to the memory of a loved one whose spirit of helping others lives on through this interface.

### 🦾 The Goal: "Hands for the Handless"
Our primary objective for the **Gemini Live Agent Challenge** is to demonstrate a profound accessibility impact. SUVI is designed to be the "hands" for those who cannot use them—individuals with motor disabilities, visual impairments, or severe accessibility needs. By using `gemini-2.5-computer-use` and `gemini-2.0-flash-live`, we are building a world where a desktop can be controlled entirely through natural voice and vision, without needing to touch a mouse or keyboard.

## ⚠️ Critical Engineering Directives (NEVER IGNORE)

1. **NO STUBS:** Always write complete, runnable, production-ready code.
2. **MODEL IDS:** Strictly use these exact Google model IDs:
   - Vision/Action: `gemini-2.5-computer-use-preview-10-2025`
   - Voice I/O: `gemini-2.0-flash-live-001`
   - Orchestrator: `gemini-2.5-pro-preview-06-05`
3. **UI CONCURRENCY:** Use `PyQt6` + `qasync`. Never block the event loop.
4. **ACCESSIBILITY FIRST:** Every 'Dangerous' action MUST have a voice confirmation loop.

## 🏗️ Architecture Layers (A2A Protocol)

1. **Orchestrator Agent (Gemini 2.5 Pro):** The brain. Plans tasks and delegates to sub-agents.
2. **Computer Use Agent (Gemini 2.5 Computer Use):** The eyes and hands. Executes vision-based loops.
3. **Live Gateway (Cloud Run):** Handles real-time voice and token verification.
4. **Local Executor (Python):** PyAutoGUI dispatcher and MSS screen capture.

## 📋 5-Day Build Plan & Task Tracker

### Day 1 — Foundation (Computer Use Loop)
- [x] Set up GCP project with real Service Accounts and Buckets.
- [x] Implement production `ActionDispatcher` with risk assessment.
- [x] Implement `ComputerUseService` with Gemini 2.5.

### Day 2 — Voice + Memory
- [x] Integrate real **Firebase Auth** for secure login.
- [x] Implement **Voice-First Confirmation** for accessibility safety.
- [x] Implement persistent memory via Firestore.

### Day 3 — Cloud Infrastructure + Gateway
- [x] Deploy FastAPI Gateway with Token Verification.
- [x] Implement **A2A (Agent-to-Agent)** handoff logic.
- [x] Deploy Orchestrator to Vertex AI Agent Engine.

### Day 4 — UI Polish + Features
- [x] Finalize `LoginWindow` and `ChatWidget` (with Autopilot support).
- [x] Implement SUVI Replay (Cloud GIF upload).
- [x] Adaptive Vision: Zoom & Re-scan capability.

### Day 5 — Demo + Submission Prep
- [ ] Record 4-minute demo video.
- [ ] Finalize Architecture diagram.
- [ ] Devpost submission.
