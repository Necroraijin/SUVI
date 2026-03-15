# from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
# import json
# import asyncio
# import os
# from typing import Dict
# from middleware.auth import verify_token
# from services.orchestrator_proxy import OrchestratorProxy

# router = APIRouter()

# # In-memory session tracking for active WebSocket connections
# # session_id -> WebSocket
# active_connections: Dict[str, WebSocket] = {}

# # Global proxy variable, will be initialized on first use to ensure .env is loaded
# _orch_proxy = None

# def get_orch_proxy():
#     global _orch_proxy
#     if _orch_proxy is None:
#         api_key = os.getenv("GEMINI_API_KEY", "")
#         if not api_key:
#             print("⚠️ WARNING: GEMINI_API_KEY not found in environment for Gateway!")
#         _orch_proxy = OrchestratorProxy(api_key=api_key)
#     return _orch_proxy

# @router.websocket("/session/{session_id}")
# async def websocket_session(websocket: WebSocket, session_id: str, token: str = Query(None)):
#     """
#     Proxies bidirectional WebSocket:
#     - Incoming from local desktop: audio chunks + state updates
#     - Outgoing to local desktop: commands from the Cloud Agent
#     """
#     # Simple auth check for hackathon: token must be provided
#     if not token:
#         await websocket.close(code=1008, reason="Authentication token missing")
#         return
        
#     try:
#         user = await verify_token(token)
#         print(f"Authenticated user {user['uid']} for session {session_id}")
#     except Exception as e:
#         await websocket.close(code=1008, reason=f"Authentication failed: {str(e)}")
#         return

#     await websocket.accept()
#     active_connections[session_id] = websocket
#     print(f"Connection established for session: {session_id}")
    
#     orch_proxy = get_orch_proxy()

#     try:
#         while True:
#             # Receive message from local desktop
#             data = await websocket.receive_text()
#             message = json.loads(data)
            
#             # Message routing logic
#             msg_type = message.get("type")
            
#             if msg_type == "ping":
#                 await websocket.send_text(json.dumps({"type": "pong"}))
            
#             elif msg_type == "telemetry":
#                 # Log to Cloud Logging / Firestore via app state
#                 print(f"Telemetry from {session_id}: {message.get('data')}")
                
#             elif msg_type == "agent_query":
#                 # Bridge to Vertex AI Orchestrator
#                 query_type = message.get("query_type") # e.g., 'plan', 'code'
#                 prompt = message.get("prompt")
#                 query_id = message.get("query_id")
#                 env_context = message.get("env_context", "")  # Get environment context from desktop app

#                 print(f"Bridging {query_type} query for session {session_id}")

#                 if query_type == "plan":
#                     result = await orch_proxy.get_plan(prompt, env_context)
#                 elif query_type == "code":
#                     result = await orch_proxy.get_code(prompt)
#                 else:
#                     result = "Unknown query type"
                    
#                 await websocket.send_text(json.dumps({
#                     "type": "agent_response",
#                     "query_id": query_id,
#                     "result": result
#                 }))

#     except WebSocketDisconnect:
#         print(f"Session {session_id} disconnected")
#         if session_id in active_connections:
#             del active_connections[session_id]
#     except Exception as e:
#         print(f"WebSocket error in {session_id}: {e}")
#         if session_id in active_connections:
#             del active_connections[session_id]

# async def broadcast_command(session_id: str, command: dict):
#     """Helper to send commands from Cloud Agent back down to the desktop client."""
#     if session_id in active_connections:
#         ws = active_connections[session_id]
#         await ws.send_text(json.dumps(command))
#         return True
#     return False
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import json
import asyncio
import os
from typing import Dict
from middleware.auth import verify_token
from services.orchestrator_proxy import OrchestratorProxy

router = APIRouter()
active_connections: Dict[str, WebSocket] = {}
_orch_proxy = None

def get_orch_proxy():
    global _orch_proxy
    if _orch_proxy is None:
        try:
            api_key = os.getenv("GEMINI_API_KEY", "")
            _orch_proxy = OrchestratorProxy(api_key=api_key)
        except Exception as e:
            print(f"⚠️ OrchestratorProxy init failed: {e}")
            _orch_proxy = None
    return _orch_proxy

# def get_orch_proxy():
#     global _orch_proxy
#     if _orch_proxy is None:
#         api_key = os.getenv("GEMINI_API_KEY", "")
#         _orch_proxy = OrchestratorProxy(api_key=api_key)
#     return _orch_proxy

async def keepalive(websocket: WebSocket, session_id: str):
    """Send a ping every 30s to prevent Cloud Run idle timeout."""
    try:
        while True:
            await asyncio.sleep(30)
            await websocket.send_text(json.dumps({"type": "ping"}))
    except Exception:
        pass

@router.websocket("/session/{session_id}")
async def websocket_session(
    websocket: WebSocket,
    session_id: str,
    token: str = Query(None)
):
    # Auth check BEFORE accept
    if not token:
        await websocket.close(code=1008, reason="Authentication token missing")
        return

    try:
        user = await verify_token(token)
    except Exception as e:
        await websocket.close(code=1008, reason=f"Auth failed: {str(e)}")
        return

    await websocket.accept()
    active_connections[session_id] = websocket
    print(f"✅ Session {session_id} connected for user {user['uid']}")

    orch_proxy = get_orch_proxy()

    # Run message handler + keepalive concurrently
    async def handle_messages():
        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                msg_type = message.get("type")

                if msg_type == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))

                elif msg_type == "pong":
                    pass  # Ignore pong responses from client

                elif msg_type == "telemetry":
                    print(f"📊 Telemetry [{session_id}]: {message.get('data')}")

                elif msg_type == "agent_query":
                    query_type = message.get("query_type")
                    prompt = message.get("prompt")
                    query_id = message.get("query_id")
                    env_context = message.get("env_context", "")

                    if query_type == "plan":
                        result = await orch_proxy.get_plan(prompt, env_context)
                    elif query_type == "code":
                        result = await orch_proxy.get_code(prompt)
                    else:
                        result = f"Unknown query type: {query_type}"

                    await websocket.send_text(json.dumps({
                        "type": "agent_response",
                        "query_id": query_id,
                        "result": result
                    }))

        except WebSocketDisconnect:
            print(f"🔌 Session {session_id} disconnected cleanly")
        except Exception as e:
            print(f"❌ WebSocket error [{session_id}]: {e}")
        finally:
            active_connections.pop(session_id, None)

    # Run both tasks — if either ends, cancel the other
    msg_task = asyncio.create_task(handle_messages())
    ping_task = asyncio.create_task(keepalive(websocket, session_id))

    done, pending = await asyncio.wait(
        [msg_task, ping_task],
        return_when=asyncio.FIRST_COMPLETED
    )
    for task in pending:
        task.cancel()

async def broadcast_command(session_id: str, command: dict):
    if session_id in active_connections:
        await active_connections[session_id].send_text(json.dumps(command))
        return True
    return False