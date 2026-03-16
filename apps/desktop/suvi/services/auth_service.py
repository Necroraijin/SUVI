import asyncio
import os
import requests
import json

class AuthService:
    """
    Handles production-grade Firebase User Authentication.
    Uses dedicated keys for Auth vs AI to ensure system robustness.
    """
    def __init__(self):
        self.current_user = None
        self.id_token = None
        self.refresh_token = None
        
        
        self.api_key = os.getenv("FIREBASE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.expected_project = os.getenv("GCP_PROJECT_ID", "project-0d0747b3-f100-478f-9b6")
        self.base_url = "https://identitytoolkit.googleapis.com/v1/accounts"

    async def login(self, email, password):
        """Authenticates with Firebase REST API."""
        if not self.api_key:
            return {"success": False, "error": "No API Key found in .env"}

        url = f"{self.base_url}:signInWithPassword?key={self.api_key}"
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        
        loop = asyncio.get_event_loop()
        try:
            response = await loop.run_in_executor(None, lambda: requests.post(url, json=payload))
            data = response.json()
            
            if response.status_code == 200:
                self.id_token = data["idToken"]
                self.refresh_token = data["refreshToken"]
                self.current_user = {
                    "uid": data["localId"],
                    "email": data["email"],
                    "display_name": data.get("displayName", email.split("@")[0])
                }
                return {"success": True, "user": self.current_user, "token": self.id_token}
            else:
                error_msg = data.get("error", {}).get("message", "Unknown Auth Error")
                return {"success": False, "error": error_msg}
        except Exception as e:
            return {"success": False, "error": f"Network Error: {str(e)}"}

    async def sign_up(self, email, password, name):
        """Creates a new Firebase user."""
        if not self.api_key:
            return {"success": False, "error": "No API Key found in .env"}

        url = f"{self.base_url}:signUp?key={self.api_key}"
        payload = {
            "email": email,
            "password": password,
            "displayName": name,
            "returnSecureToken": True
        }
        
        loop = asyncio.get_event_loop()
        try:
            response = await loop.run_in_executor(None, lambda: requests.post(url, json=payload))
            data = response.json()
            
            if response.status_code == 200:
                return {"success": True, "message": "Account created! Please log in."}
            else:
                error_msg = data.get("error", {}).get("message", "Unknown Signup Error")
                return {"success": False, "error": error_msg}
        except Exception as e:
            return {"success": False, "error": f"Signup Error: {str(e)}"}

    def get_id_token(self):
        return self.id_token

    def get_current_user_id(self):
        return self.current_user["uid"] if self.current_user else "guest"
