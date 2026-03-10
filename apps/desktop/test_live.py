import asyncio
from google import genai
from google.genai import types

async def test():
    client = genai.Client(http_options={'api_version':'v1alpha'})
    models = client.models.list()
    config = types.LiveConnectConfig(
        response_modalities=[types.Modality.AUDIO],
        tools=[types.Tool(
            function_declarations=[
                types.FunctionDeclaration(name='test_func', description='test')
            ]
        )]
    )
    for model in models:
        if 'bidiGenerateContent' in getattr(model, 'supported_actions', []) or 'bidi' in str(getattr(model, 'supported_actions', '')):
            try:
                print(f'Testing {model.name}...')
                async with client.aio.live.connect(model=model.name, config=config) as session:
                    print(f'SUCCESS: {model.name} works with tools!')
                    break
            except Exception as e:
                print(f'FAILED {model.name}: {e}')

asyncio.run(test())