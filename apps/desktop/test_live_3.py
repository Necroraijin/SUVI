import asyncio
from google import genai
from google.genai import types

async def test():
    client = genai.Client(http_options={'api_version':'v1alpha'})
    
    models = ['gemini-2.0-flash-live-001']
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
    
    for model in models:
        try:
            print(f"Testing {model}...")
            async with client.aio.live.connect(model=model, config=config):
                print(f"SUCCESS: {model} supports Live API!")
        except Exception as e:
            print(f"ERROR on {model}: {e}")

asyncio.run(test())