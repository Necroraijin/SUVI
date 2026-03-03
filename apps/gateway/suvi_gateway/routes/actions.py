from fastapi import APIRouter

router = APIRouter()

@router.post("/actions/log")
async def log_action(payload: dict):
    """
    Endpoint for the desktop to report back when it finishes an action 
    (like successfully clicking the mouse or reading a file).
    """
    action = payload.get("action")
    status = payload.get("status")
    print(f"[Desktop Callback] Action '{action}' reported status: {status}")
    return {"acknowledged": True}