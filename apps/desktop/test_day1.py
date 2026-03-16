import asyncio
import os
import sys
from dotenv import load_dotenv
from google import genai


sys.path.append(os.path.dirname(__file__))

from suvi.services.computer_use_service import ComputerUseService


root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
load_dotenv(os.path.join(root_dir, '.env'))

async def main():
    
    api_key = os.getenv("GEMINI_API_KEY")
    project_id = os.getenv("GCP_PROJECT_ID")
    location = os.getenv("GCP_LOCATION", "us-central1")
    
    if api_key and api_key != "<your_key>":
        print("✅ Initializing AI Studio GenAI Client...")
        client = genai.Client(api_key=api_key, http_options={'api_version': 'v1alpha'})
    elif project_id:
        print(f"✅ Initializing Vertex AI Client for Project: {project_id}")
        client = genai.Client(vertexai=True, project=project_id, location=location)
    else:
        print("❌ ERROR: Neither GEMINI_API_KEY nor GCP_PROJECT_ID is set.")
        return
    service = ComputerUseService(client)
    
    intent = "Click the Windows Start button on the taskbar."
    print(f"🤖 Testing SUVI Computer Use Loop (Vertex AI Preview)...\n🎯 Intent: {intent}\n")
    
    def on_action(desc):
        print(f"  [ACTION] Executing: {desc}")
        
    def on_screenshot(img_bytes):
        print(f"  [VISION] Captured screen frame ({len(img_bytes)} bytes) - Sending to Gemini 2.5 Preview...")

    try:
        result = await service.execute_task(
            intent=intent,
            user_id="test_user",
            session_id="test_session",
            on_action=on_action,
            on_screenshot=on_screenshot
        )
        
        if result.get("success"):
            print("\n✅ Task completed successfully!")
            print(f"Actions taken: {len(result.get('actions_taken', []))}")
        else:
            print(f"\n⚠️ Task stopped: {result.get('reason')}")
            
    except Exception as e:
        print(f"\n❌ Loop failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
