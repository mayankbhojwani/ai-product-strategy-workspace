import asyncio
from app.config import get_model_client
from autogen_core.models import UserMessage

async def test():
    client = get_model_client()

    response = await client.create(
        messages=[
            UserMessage(content="Say hello in one sentence.", source="user")
        ]
    )

    print(response)

asyncio.run(test())
