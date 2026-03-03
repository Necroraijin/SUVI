from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from suvi_gateway.connections import ConnectionManager
from suvi_gateway.routes import health, live_token, actions, agents

app = FastAPI(title="SUVI Cloud Run Gateway", version="2.0.0")
manager = ConnectionManager()

# Include the external routes
app.include_router(health.router)
app.include_router(live_token.router)
app.include_router(actions.router)
app.include_router(agents.router)

@app.websocket("/ws/desktop")
async def desktop_endpoint(websocket: WebSocket):
    """The secure WebSocket connection for the desktop app."""
    client_id = await manager.connect(websocket)
    print(f"[{client_id}] Desktop connected to Cloud Gateway.")
    
    try:
        while True:
            data = await websocket.receive_text()
            print(f"[Gateway] Received from Desktop: {data}")
            
            # Simple echo for testing the connection
            await manager.send_message(f"Gateway received: {data}", websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"[{client_id}] Desktop disconnected.")