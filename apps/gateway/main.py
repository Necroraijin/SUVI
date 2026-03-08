from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os
from dotenv import load_dotenv

from routes import ws_proxy
from services.firestore import FirestoreService
from services.cloud_logging import ActionLogger

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize services
    app.state.firestore = FirestoreService()
    app.state.logger = ActionLogger()
    print("SUVI Gateway started — Cloud Run instance ready")
    yield
    print("SUVI Gateway shutting down")

app = FastAPI(
    title="SUVI Gateway",
    description="Cloud Run gateway — WebSocket proxy, auth, session management",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ws_proxy.router, prefix="/ws")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "project_id": os.getenv("GCP_PROJECT_ID")}

if __name__ == "__main__":
    # For local testing
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
