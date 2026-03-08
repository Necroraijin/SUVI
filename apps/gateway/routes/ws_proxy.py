from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import asyncio
from typing import Dict

router = APIRouter()

# In-memory session tracking for active WebSocket connections
# session_id -> WebSocket
active_connections: Dict[str, WebSocket] = {}

@router.websocket("/session/{session_id}")
async def websocket_session(websocket: WebSocket, session_id: str):
    """
    Proxies bidirectional WebSocket:
    - Incoming from local desktop: audio chunks + state updates
    - Outgoing to local desktop: commands from the Cloud Agent
    """
    await websocket.accept()
    active_connections[session_id] = websocket
    print(f"Connection established for session: {session_id}")

    try:
        while True:
            # Receive message from local desktop
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Message routing logic
            msg_type = message.get("type")
            
            if msg_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
            
            elif msg_type == "telemetry":
                # Log to Cloud Logging / Firestore via app state
                pass
                
            elif msg_type == "agent_query":
                # Bridge to Vertex AI Orchestrator
                pass

    except WebSocketDisconnect:
        print(f"Session {session_id} disconnected")
        if session_id in active_connections:
            del active_connections[session_id]
    except Exception as e:
        print(f"WebSocket error in {session_id}: {e}")
        if session_id in active_connections:
            del active_connections[session_id]

async def broadcast_command(session_id: str, command: dict):
    """Helper to send commands from Cloud Agent back down to the desktop client."""
    if session_id in active_connections:
        ws = active_connections[session_id]
        await ws.send_text(json.dumps(command))
        return True
    return False
