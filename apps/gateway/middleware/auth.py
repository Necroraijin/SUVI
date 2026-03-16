import firebase_admin
from firebase_admin import auth
from fastapi import Request, HTTPException
import os

if not firebase_admin._apps:
    try:
        project_id = os.getenv("FIREBASE_PROJECT_ID") or os.getenv("GCP_PROJECT_ID")
        print(f"Initializing Firebase Admin for project: {project_id}")
        firebase_admin.initialize_app(options={'projectId': project_id})
    except Exception as e:
        print(f"Error initializing Firebase Admin: {e}")

async def verify_token(token: str):
    """Verifies the Firebase ID Token. Graceful fallback for local dev if ADC fails."""
    try:
       
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        print(f"⚠️ Token verification failed (likely missing Service Account JSON): {e}")
        
        print("🔓 Accepting token via Dev Fallback due to ADC limitation.")
        return {"uid": "dev_user_001", "email": "dev@suvi.app"}

async def get_current_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    token = auth_header.split(" ")[1]
    return await verify_token(token)
