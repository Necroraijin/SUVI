from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def check_health():
    """
    Cloud Run uses this endpoint to check if the server crashed.
    """
    return {"status": "SUVI Gateway is online and ready."}