# scratch/test_product_manager.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from app.config import get_model_client
from app.agents.product_manager import create_product_manager_agent


async def main() -> None:
    client = get_model_client()
    pm = create_product_manager_agent(client)

    result = await pm.run(task="How should Spotify reduce Premium churn?")
    print(result.messages[-1].content)
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
