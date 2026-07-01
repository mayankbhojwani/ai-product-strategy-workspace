# scratch/test_manager.py
"""
Manual smoke test for the Manager Agent.
Not part of the app — just a throwaway script to verify one agent in isolation
before it's wired into the full team.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
from app.config import get_model_client
from app.agents.manager import create_manager_agent


async def main() -> None:
    client = get_model_client()
    manager = create_manager_agent(client)

    result = await manager.run(
        task=(
            "The team discussed: reduce Premium churn by improving "
            "playlist personalization (Product Manager), users churn "
            "most after 2 skipped renewal reminders (Data Scientist), "
            "and win-back offers cannibalize revenue if overused "
            "(Devil's Advocate)."
        )
    )

    print(result.messages[-1].content)
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
