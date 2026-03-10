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

    async def _listen(self):
        try:
            async for message in self.ws:
                data = json.loads(message)
                if data.get("type") == "agent_response":
                    query_id = data.get("query_id")
                    if query_id and query_id in self._pending_queries:
                        self._pending_queries[query_id].set_result(data.get("result", ""))
                    else:
                        # Fallback if no query_id is returned
                        print(f"📥 Received from Gateway: {data}")
                        # Resolve the first pending query just in case
                        if self._pending_queries:
                            first_key = list(self._pending_queries.keys())[0]
                            self._pending_queries[first_key].set_result(data.get("result", ""))
                else:
                    print(f"📥 Received from Gateway: {data}")
        except Exception as e:
            print(f"⚠️ Gateway connection lost: {e}")

    async def send_telemetry(self, data: dict):
        if self.ws:
            await self.ws.send(json.dumps({
                "type": "telemetry",
                "data": data
            }))

    async def query_orchestrator(self, query_type: str, prompt: str) -> str:
        """Sends a query to the orchestrator via the gateway proxy and awaits the result."""
        if not self.ws:
            return "Error: Not connected to gateway"
            
        self._query_counter += 1
        query_id = f"q_{self._query_counter}"
        
        future = asyncio.get_event_loop().create_future()
        self._pending_queries[query_id] = future
            
        await self.ws.send(json.dumps({
            "type": "agent_query",
            "query_id": query_id,
            "query_type": query_type,
            "prompt": prompt
        }))
        
        try:
            # Wait up to 60 seconds for the cloud agent to respond
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
