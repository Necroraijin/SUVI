import asyncio
import json
import websockets
import os

class GatewayService:
    """
    Manages the persistent connection between the Desktop App and the Cloud Gateway.
    Proxies orchestrator requests and sends telemetry.
    """
    def __init__(self):
        self.ws = None
        self.gateway_url = os.getenv("GATEWAY_URL", "ws://localhost:8080/ws/session")
        self.token = "mock_token" # In reality, fetched from AuthService
        self.session_id = "default_session"
        self._pending_queries = {}
        self._query_counter = 0

    async def connect(self, session_id: str, token: str):
        self.session_id = session_id
        self.token = token
        
        url = f"{self.gateway_url}/{session_id}?token={token}"
        print(f"🔗 Connecting to Gateway at {url}...")
        
        try:
            self.ws = await websockets.connect(url)
            print("✅ Connected to Gateway.")
            asyncio.create_task(self._listen())
        except Exception as e:
            print(f"❌ Failed to connect to Gateway: {e}")

    @property
    def is_connected(self) -> bool:
        """Reliable check: ws exists and appears connected."""
        if self.ws is None:
            return False
        try:
            # websockets v12+ uses .state, older uses .open
            if hasattr(self.ws, 'open'):
                return self.ws.open
            # For newer websockets, check if state is OPEN
            import websockets.connection
            return self.ws.state == websockets.connection.State.OPEN
        except Exception:
            return False

    async def _listen(self):
        try:
            async for message in self.ws:
                data = json.loads(message)
                if data.get("type") == "agent_response":
                    query_id = data.get("query_id")
                    if query_id and query_id in self._pending_queries:
                        self._pending_queries[query_id].set_result(data.get("result", ""))
                    else:
                        print(f"📥 Received from Gateway: {data}")
                        if self._pending_queries:
                            first_key = list(self._pending_queries.keys())[0]
                            self._pending_queries[first_key].set_result(data.get("result", ""))
                else:
                    print(f"📥 Received from Gateway: {data}")
        except Exception as e:
            print(f"⚠️ Gateway connection lost: {e}")
        finally:
            # CRITICAL: Clear the stale reference so we don't route through a dead socket
            self.ws = None
            # Fail any pending queries so they don't hang forever
            for qid, future in list(self._pending_queries.items()):
                if not future.done():
                    future.set_result("Error: Gateway connection lost")
            self._pending_queries.clear()
            print("🔌 Gateway WebSocket reference cleared.")

    async def send_telemetry(self, data: dict):
        if self.ws:
            await self.ws.send(json.dumps({
                "type": "telemetry",
                "data": data
            }))

    async def query_orchestrator(self, query_type: str, prompt: str) -> str:
        """Sends a query to the orchestrator via the gateway proxy and awaits the result."""
        if not self.is_connected:
            return "Error: Not connected to gateway"
            
        self._query_counter += 1
        query_id = f"q_{self._query_counter}"
        
        future = asyncio.get_event_loop().create_future()
        self._pending_queries[query_id] = future
        
        try:
            await self.ws.send(json.dumps({
                "type": "agent_query",
                "query_id": query_id,
                "query_type": query_type,
                "prompt": prompt
            }))
        except Exception as e:
            # WebSocket died between the is_connected check and the send
            self._pending_queries.pop(query_id, None)
            self.ws = None
            print(f"⚠️ Gateway send failed: {e}")
            return f"Error: Gateway send failed: {e}"
        
        try:
            result = await asyncio.wait_for(future, timeout=60.0)
            return result
        except asyncio.TimeoutError:
            return "Error: Gateway orchestrator request timed out."
        finally:
            self._pending_queries.pop(query_id, None)
        
    async def disconnect(self):
        if self.ws:
            await self.ws.close()
            print("Disconnected from Gateway.")
