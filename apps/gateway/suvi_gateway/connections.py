from fastapi import WebSocket
import uuid

class ConnectionManager:
    """Safely manages active WebSocket connections to prevent memory leaks and handle disconnects."""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> str:
        await websocket.accept()
        self.active_connections.append(websocket)
        # Generate a session ID for tracking/telemetry
        return str(uuid.uuid4())

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        """Sends a JSON string directly to a specific connected desktop client."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            print(f"[Manager Error] Failed to send message: {e}")
            self.disconnect(websocket)