import asyncio
import websockets
import json
from PyQt6.QtCore import QObject, pyqtSignal
from apps.desktop.suvi.ui.action_ring.ring_state import RingState

class LiveSession(QObject):
    """Manages the bidirectional WebSocket stream with Gemini Live."""
    
    # Signals to safely communicate back to the PyQt6 UI thread
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    state_changed = pyqtSignal(object) # Emits RingState
    transcript_ready = pyqtSignal(str)
    audio_received = pyqtSignal(bytes)
    tool_call_received = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    # Map tool names to Ring Segment indices for visual feedback
    TOOL_TO_SEGMENT = {
        "mouse_click": 5,      # 'app'
        "type_text": 2,        # 'write'
        "press_hotkey": 5,     # 'app'
        "read_file": 4,        # 'file'
        "write_file": 4,       # 'file'
        "list_directory": 4,   # 'file'
        "browser_navigate": 1, # 'browse'
        "browser_read": 1,     # 'browse'
    }

    def __init__(self, gateway_client):
        super().__init__()
        self.gateway = gateway_client
        self.ws = None
        self._listen_task = None

    async def connect(self):
        """Fetches the token and opens the WebSocket stream."""
        try:
            ws_url = await self.gateway.get_live_token()
            print(f"[LiveSession] Connecting to Gemini Live WebSockets: {ws_url}")
            
            self.ws = await websockets.connect(ws_url)
            self._listen_task = asyncio.create_task(self._listen_loop())
            
            self.connected.emit()
            self.state_changed.emit(RingState.LISTENING)
            print("[LiveSession] Stream established. SUVI is listening.")
            
        except Exception as e:
            print(f"[LiveSession] Connection failed: {e}")
            self.error_occurred.emit(str(e))
            self.state_changed.emit(RingState.ERROR)

    async def _listen_loop(self):
        """Background loop waiting for Gemini to speak or trigger a tool."""
        try:
            async for message in self.ws:
                data = json.loads(message)
                
                # Handle Model Turn (Speech)
                if "serverContent" in data:
                    content = data["serverContent"]
                    if "modelTurn" in content:
                        parts = content["modelTurn"].get("parts", [])
                        for part in parts:
                            if "inlineData" in part:
                                # TTS Audio from Gemini
                                self.audio_received.emit(bytes.frombase64(part["inlineData"]["data"]))
                            if "text" in part:
                                self.transcript_ready.emit(part["text"])

                # Handle Tool Calls
                elif "toolCall" in data:
                    calls = data["toolCall"].get("functionCalls", [])
                    for call in calls:
                        print(f"[LiveSession] Tool Call: {call['name']}")
                        self.state_changed.emit(RingState.THINKING)
                        self.tool_call_received.emit(call)
                
                # Handle Setup Completion
                elif "setupComplete" in data:
                    print("[LiveSession] Setup complete received.")

        except websockets.exceptions.ConnectionClosed:
            print("[LiveSession] Stream closed by server.")
            self.disconnected.emit()
            self.state_changed.emit(RingState.IDLE)
        except Exception as e:
            print(f"[LiveSession] Listener error: {e}")
            self.error_occurred.emit(str(e))

    async def send_audio_chunk(self, pcm_bytes: bytes):
        """Pushes raw microphone data to Vertex AI."""
        if self.ws and self.ws.open:
            import base64
            payload = {
                "realtimeInput": {
                    "mediaChunks": [{
                        "mimeType": "audio/pcm;rate=16000",
                        "data": base64.b64encode(pcm_bytes).decode('utf-8')
                    }]
                }
            }
            await self.ws.send(json.dumps(payload))

    async def disconnect(self):
        if self.ws:
            await self.ws.close()
            self.ws = None
        if self._listen_task:
            self._listen_task.cancel()
        self.disconnected.emit()
        self.state_changed.emit(RingState.IDLE)