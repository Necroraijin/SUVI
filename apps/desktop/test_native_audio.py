import asyncio
import os
from google import genai
from google.genai import types

async def test():
    client = genai.Client()
    config = types.LiveConnectConfig(
        response_modalities=[types.Modality.AUDIO]
    )
    print("Connecting...")
    try:
        async with client.aio.live.connect(model='gemini-2.5-flash-native-audio-latest', config=config) as session:
            print('Connected')
            await asyncio.sleep(1)
            print('Sending audio...')
            await session.send_realtime_input(
                media=types.Blob(data=b'\x00' * 3200, mime_type="audio/pcm;rate=16000")
            )
            print('Audio sent. Waiting for response...')
            async for response in session.receive():
                print("Response received:", response)
    except Exception as e:
        print("ERROR:", e)

asyncio.run(test())
