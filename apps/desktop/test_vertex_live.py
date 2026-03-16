import asyncio
import os
os.environ['GOOGLE_CLOUD_PROJECT']='project-0d0747b3-f100-478f-9b6'
from google import genai
from google.genai import types

async def test():
    client = genai.Client(vertexai=True, location='us-central1')
    print("Testing gemini-2.0-flash-001...")
    try:
        config = types.LiveConnectConfig(
            response_modalities=[types.Modality.AUDIO],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name='Aoede'
                    )
                )
            )
        )
        async with client.aio.live.connect(model='gemini-2.5-flash', config=config):
            print('SUCCESS: connected to gemini-2.5-flash via Vertex AI')
    except Exception as e:
        print('ERROR:', e)

asyncio.run(test())