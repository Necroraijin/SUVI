import asyncio
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

async def main():
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key, http_options={'api_version': 'v1alpha'})
    
    m = "gemini-2.5-flash-native-audio-preview-12-2025"
    
    try:
        config = types.LiveConnectConfig(
            response_modalities=[types.Modality.AUDIO, types.Modality.TEXT]
        )
        print("Testing with AUDIO and TEXT modalities...")
        async with client.aio.live.connect(model=m, config=config) as session:
            print("✅ Connected!")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())