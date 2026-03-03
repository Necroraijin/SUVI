import os
import aiohttp
from fastapi import APIRouter, Request, HTTPException

router = APIRouter()

# Map agent names to their internal Docker/localhost ports or Cloud Run URLs
# In a real Cloud Run deployment, these would point to internal service URLs
AGENT_URLS = {
    "text": os.environ.get("TEXT_AGENT_URL", "http://localhost:8002"),
    "code": os.environ.get("CODE_AGENT_URL", "http://localhost:8003"),
    "browser": os.environ.get("BROWSER_AGENT_URL", "http://localhost:8004"),
    "search": os.environ.get("SEARCH_AGENT_URL", "http://localhost:8005"),
    "memory": os.environ.get("MEMORY_AGENT_URL", "http://localhost:8006"),
    "data": os.environ.get("DATA_AGENT_URL", "http://localhost:8007"),
}

@router.post("/agents/{agent_name}")
async def proxy_a2a_request(agent_name: str, request: Request):
    """
    A2A Proxy Endpoint
    Proxies JSON-RPC (or raw HTTP) requests to the correct internal sub-agent.
    """
    target_url = AGENT_URLS.get(agent_name.lower())
    
    if not target_url:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found.")
        
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
    print(f"[Gateway] Proxying A2A request to {agent_name} -> {target_url}")
    
    # We strip the trailing slash for clean appending if needed
    target_url = target_url.rstrip('/')
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(target_url, json=payload) as response:
                if response.status != 200:
                    error_msg = await response.text()
                    raise HTTPException(status_code=response.status, detail=f"Agent Error: {error_msg}")
                    
                result = await response.json()
                return result
                
    except aiohttp.ClientError as e:
        print(f"[Gateway] Failed to reach {agent_name}: {e}")
        raise HTTPException(status_code=503, detail=f"Agent service unavailable: {e}")
