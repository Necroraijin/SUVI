import asyncio
import json
import aiohttp
import os

class GatewayClient:
    """Handles REST communication with the SUVI Cloud Run Gateway."""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        # In production, this should be stored securely or retrieved via OAuth
        self.client_secret = "suvi-hackathon-secret-123"

    async def get_live_token(self) -> str:
        """
        Asks the Token Vending Machine for a secure Gemini Live WebSocket URL.
        Returns the full WebSocket URL with the access token.
        """
        url = f"{self.base_url}/auth/live-token"
        print(f"[GatewayClient] Requesting secure Vertex AI token from {url}...")
        
        headers = {
            "X-Suvi-Client-Auth": self.client_secret,
            "Accept": "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Gateway error ({response.status}): {error_text}")
                    
                    data = await response.json()
                    token = data.get("token")
                    endpoint = data.get("endpoint")
                    
                    # Gemini Live API expects the token either in a header or as a query param
                    # For WebSockets, it's often passed as a query param 'access_token'
                    # Or 'key' if using an API Key. For Vertex AI it's 'access_token'.
                    ws_url = f"{endpoint}?access_token={token}"
                    
                    print("[GatewayClient] Secure token received and URL assembled.")
                    return ws_url

        except Exception as e:
            print(f"[GatewayClient] Request failed: {e}")
            # Fallback for local UI testing if gateway is not running
            return "wss://generativelanguage.googleapis.com/ws/mock-connection"
