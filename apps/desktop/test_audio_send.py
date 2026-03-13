import asyncio
from google import genai
from google.genai import types

async def test():
    client = genai.Client(http_options={'api_version':'v1alpha'})
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
    try:
        async with client.aio.live.connect(model='gemini-2.0-flash-live-001', config=config) as session:
            print("Connected.")
            await session.send(input=types.LiveClientRealtimeInput(
                media_chunks=[types.Blob(data=b'000', mime_type='audio/pcm;rate=16000')]
            ))
            print("Audio sent. Waiting for response...")
            # Try with the raw dict format if the above fails?
            # await session.send(input={"data": b'000', "mime_type": "audio/pcm;rate=16000"})
    except Exception as e:
        print('ERROR:', type(e), e)

asyncio.run(test())