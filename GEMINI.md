# SUVI Project Status & Roadmap (GEMINI.md)

## Project Overview

**SUVI (Superintelligent Unified Voice Interface)** is a production-grade, multi-agent AI desktop control system. It uses a **PyQt6** native frontend for a single-process execution model, eliminating IPC overhead, and leverages **Vertex AI** for agent intelligence.

---

## Current Status: 🚀 Integrated, but Needs ML Hardening

The core frontend-to-backend pipeline is successfully wired. SUVI can capture voice, route it through the gateway, enforce permission tiers, and execute UI/system actions. However, the system currently lacks true distributed A2A listening, proper Vertex AI RAG, and function-calling at the sub-agent layer.

To win the Google Hackathon, SUVI must transition from a "Text-Generating System" to a "True Multi-Agent Function-Calling System".

### ✅ Implemented Features

- **PyQt6 UI Layer:** Action Ring (custom QPainter), System Tray, Micro-Toasts, Result Cards.
- **Desktop Workers:** `VoiceWorker` (mic capture), `WakeWordWorker` (hotkey), `ScreenWorker` (mss).
- **Core Connectivity:** `LiveSession` connects to Gemini Live API; Token vending works.
- **Security:** `PermissionTier` model with active `ConfirmDialog` enforcement.
- **Telemetry & Memory:** Firestore and BigQuery client wrappers implemented.

### ❌ Critical Gaps Found in AI/ML Review (Bugs & Missing Features)

1. **The A2A Server Gap (Major Bug):** `TaskRouter` sends requests to `http://localhost:8001/agent_...` using `A2AClient`, but the sub-agents (e.g., `TextAgent`, `CodeAgent`) only inherit from `GeminiAgent`. They do not instantiate `A2AServer` to listen for these incoming HTTP requests. The routing will currently fail with a Connection Refused error.
2. **Missing Gemini Tool Binding:** Sub-agents currently process tasks by interpolating text into strings (e.g., `prompt = f"Summarize {text}"`) and calling `generate()`. To be a true ADK/Vertex AI project, they must bind their methods as explicit `tools` using `types.Tool` and `types.FunctionDeclaration` in the `GenerateContentConfig`.
3. **Mocked Code RAG (Not Production Grade):** `agents/code_agent/rag/indexer.py` currently reads the first 1,000 characters of local files into a python dictionary. To win a Vertex AI hackathon, this *must* be upgraded to use Vertex AI Vector Search (or at least local embeddings via `text-embedding-004` + FAISS/Chroma).
4. **Mocked Deployments:** The deployment scripts (like `deploy_orchestrator` in `agents/orchestrator/deploy.py`) are print-statement stubs. They do not actually interact with Google Cloud or Vertex AI Agent Engine.
5. **No Retry Logic:** The distributed A2A calls lack exponential backoff (e.g., using the `tenacity` library), making the multi-agent system brittle to network blips.

---

## 🛠️ Immediate Roadmap (Next Steps)

### Phase 1: The "Grand Wiring"

- [x] **Bridge Voice to AI:** Connect `VoiceWorker.audio_chunk_ready` -> `LiveSession.send_audio_chunk`.
- [x] **Bridge AI to UI:** Connect `LiveSession.state_changed` -> `RingWindow.transition_to`.
- [x] **Bridge AI to Execution:** Connect `LiveSession.tool_call_received` -> `ActionExecutor.execute_tool_call`.
- [x] **Live Session Implementation:** Uncomment and fix `LiveSession.connect()` logic.

### Phase 2: Backend & Protocol Alignment

- [x] **A2A Integration:** Refactor `agents/shared/a2a_client.py` to use the real `shared/a2a` protocol.
- [x] **Gateway Token Vending:** Implement real token fetching.
- [x] **Memory & Telemetry:** Implement the Firestore and BigQuery clients.

### Phase 3: Security & Polish

- [x] **Permission Tiers:** Implement the "Confirm Dialog" for Tier 3+ actions.
- [x] **Visual Polish:** Wire `VoiceWorker.amplitude_changed` to the Action Ring's pulse animation.

### Phase 4: True ML & Agentic Upgrades (HACKATHON WINNERS)

- [x] **A2A Servers:** Wrap all sub-agents (`CodeAgent`, `TextAgent`, etc.) in the `A2AServer` class so they can bind to ports and actually receive tasks from the Orchestrator.
- [x] **Tool Binding:** Refactor `GeminiAgent` in `agent_utils.py` to accept and bind Python functions as Gemini Tools, allowing the model to decide *how* to execute sub-tasks.
- [x] **Vertex AI Vector Search:** Rewrite `CodeIndexer` to generate embeddings (`text-embedding-004`) and push them to a Vector DB for semantic code retrieval.
- [x] **Robust Routing:** Add `tenacity` retry wrappers to the `A2AClient` requests.

### Phase 5: Cloud Deployment & Hardening

- [x] **Gateway A2A Proxy:** Expose the A2A routing through the FastAPI Gateway so agents don't rely on `localhost:8001` in production.
- [x] **Deploy Scripts:** Write actual `gcloud` or `google-cloud-aiplatform` python deployment logic in the `scripts/` directory.

---

## ⚠️ Known Issues / Bugs

- Sub-agents currently operate as standalone prompt-wrappers rather than actively listening server nodes.
- Gateway WebSocket logic echoes text back; it needs to be strictly bound as a pass-through to Gemini Live if it intercepts tool calls.

---

*Last Updated: 2026-03-03*
