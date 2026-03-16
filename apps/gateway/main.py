
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from dotenv import load_dotenv

from routes import ws_proxy
from services.firestore import FirestoreService
from services.cloud_logging import ActionLogger

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
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
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ws_proxy.router, prefix="/ws")

@app.get("/")
async def root():
    return {"message": "SUVI Gateway is running", "status": "ok"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "project_id": os.getenv("GCP_PROJECT_ID")}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)