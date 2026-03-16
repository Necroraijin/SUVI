import asyncio
import json
import websockets
import os

class GatewayService:
    """
    Persistent connection between Desktop SUVI and Cloud Gateway.
    Handles orchestrator queries and telemetry.
    """

    def __init__(self):
        self.ws = None
        self.gateway_url = os.getenv(
            "GATEWAY_URL",
            "wss://suvi-google-gemini-live-hackathon-722150734142.us-central1.run.app/ws/session"
        )
        self.session_id = None
        self.token = None
        self._pending_queries = {}
        self._query_counter = 0
        self._listen_task = None
        self._ping_task = None

    # -----------------------------------------------------------
    # CONNECTION
    # -----------------------------------------------------------
    async def connect(self, session_id: str, token: str):
        self.session_id = session_id
        self.token = token
        url = f"{self.gateway_url}/{session_id}?token={token}"
        print(f"🔗 Connecting to Gateway: {url}")

        try:
            self.ws = await websockets.connect(
                url,
                ping_interval=None,  
                max_size=10_000_000
            )
            print("✅ Connected to Gateway.")
            self._listen_task = asyncio.create_task(self._listen())
            self._ping_task = asyncio.create_task(self._ping_loop())
        except Exception as e:
            print(f"❌ Gateway connection failed: {e}")
            self.ws = None

    # -----------------------------------------------------------
    # CONNECTION STATE
    # -----------------------------------------------------------
    @property
    def is_connected(self) -> bool:
        if self.ws is None:
            return False
        try:
            if hasattr(self.ws, "open"):
                return self.ws.open
            import websockets.connection
            return self.ws.state == websockets.connection.State.OPEN
        except Exception:
            return False

    # -----------------------------------------------------------
    # LISTENER
    # -----------------------------------------------------------
    async def _listen(self):
        try:
            async for message in self.ws:
                data = json.loads(message)
                msg_type = data.get("type")

                if msg_type == "agent_response":
                    query_id = data.get("query_id")
                    if query_id in self._pending_queries:
                        future = self._pending_queries.pop(query_id)
                        if not future.done():
                            future.set_result(data.get("result", ""))
                elif msg_type == "ping":
                    
                    pass
                else:
                    print("📥 Gateway message:", data)
        except Exception as e:
            print(f"⚠️ Gateway connection lost: {e}")
        finally:
            await self._handle_disconnect()

    # -----------------------------------------------------------
    # PING LOOP (prevents Cloud Run idle timeout)
    # -----------------------------------------------------------
    async def _ping_loop(self):
        while self.is_connected:
            try:
                await asyncio.sleep(20)
                await self.ws.send(json.dumps({"type": "ping"}))
            except Exception:
                break

    # -----------------------------------------------------------
    # SEND TELEMETRY
    # -----------------------------------------------------------
    async def send_telemetry(self, data: dict):
        if not self.is_connected:
            return
        try:
            await self.ws.send(json.dumps({
                "type": "telemetry",
                "data": data
            }))
        except Exception:
            await self._handle_disconnect()

    # -----------------------------------------------------------
    # ORCHESTRATOR QUERY
    # -----------------------------------------------------------
    async def query_orchestrator(
        self,
        query_type: str,
        prompt: str,
        env_context: str = ""
    ) -> str:
        if not self.is_connected:
            return "Error: Gateway not connected"

        self._query_counter += 1
        query_id = f"q_{self._query_counter}"

        loop = asyncio.get_event_loop()
        future = loop.create_future()
        self._pending_queries[query_id] = future

        try:
            await self.ws.send(json.dumps({
                "type": "agent_query",
                "query_id": query_id,
                "query_type": query_type,
                "prompt": prompt,
                "env_context": env_context
            }))
        except Exception as e:
            self._pending_queries.pop(query_id, None)
            await self._handle_disconnect()
            return f"Gateway send error: {e}"

        try:
            return await asyncio.wait_for(future, timeout=60)
        except asyncio.TimeoutError:
            self._pending_queries.pop(query_id, None)
            return "Gateway request timeout"

    # -----------------------------------------------------------
    # CLEAN DISCONNECT
    # -----------------------------------------------------------
    async def _handle_disconnect(self):
        if self.ws:
            try:
                await self.ws.close()
            except Exception:
                pass
        self.ws = None

        for future in self._pending_queries.values():
            if not future.done():
                future.set_result("Error: Gateway connection lost")

        self._pending_queries.clear()
        print("🔌 Gateway connection closed.")

    async def disconnect(self):
        if self.ws:
            await self.ws.close()
        if self._listen_task:
            self._listen_task.cancel()
        if self._ping_task:
            self._ping_task.cancel()
        print("Gateway disconnected.")
