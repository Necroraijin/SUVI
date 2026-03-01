import asyncio
import websockets
import json
from PyQt6.QtCore import QObject, pyqtSignal

class LiveSession(QObject):
    """Manages the bidirectional WebSocket stream with Gemini Live."""
    
    # Signals to safely communicate back to the PyQt6 UI thread
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    audio_received = pyqtSignal(bytes)
    tool_call_received = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, gateway_client):
        super().__init__()
        self.gateway = gateway_client
        self.ws = None
        self._listen_task = None

    async def connect(self):
        """Fetches the token and opens the WebSocket stream."""
        try:
            ws_url = await self.gateway.get_live_token()
            print(f"[LiveSession] Connecting to Gemini Live WebSockets...")
            
            # TODO: Uncomment the actual connection logic once we have a real token
            # self.ws = await websockets.connect(ws_url)
            # self._listen_task = asyncio.create_task(self._listen_loop())
            
            self.connected.emit()
            print("[LiveSession] Stream established. SUVI is listening.")
            
        except Exception as e:
            print(f"[LiveSession] Connection failed: {e}")
            self.error_occurred.emit(str(e))

    async def _listen_loop(self):
        """Background loop waiting for Gemini to speak or trigger a tool."""
        try:
            async for message in self.ws:
                data = json.loads(message)
                
                if "audio" in data:
                    # Emit raw PCM bytes for the desktop speaker to play
                    self.audio_received.emit(bytes.fromhex(data["audio"]))
                    
                elif "toolCall" in data:
                    # Emit JSON command for the Action Executor
                    print(f"[LiveSession] Tool Call received: {data['toolCall']['name']}")
                    self.tool_call_received.emit(data["toolCall"])
                    
        except websockets.exceptions.ConnectionClosed:
            print("[LiveSession] Stream closed by server.")
            self.disconnected.emit()

    async def send_audio_chunk(self, pcm_bytes: bytes):
        """Pushes raw microphone data to Vertex AI."""
        if self.ws and not self.ws.closed:
            # We will format this into the exact JSON envelope Vertex AI expects
            payload = json.dumps({"realtimeInput": {"mediaChunks": [{"mimeType": "audio/pcm", "data": pcm_bytes.hex()}]}})
            await self.ws.send(payload)

    async def disconnect(self):
        if self.ws:
            await self.ws.close()
            self.ws = None
        if self._listen_task:
            self._listen_task.cancel()
        self.disconnected.emit()