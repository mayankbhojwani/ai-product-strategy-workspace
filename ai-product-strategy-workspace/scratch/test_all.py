# scratch/test_team.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from app.orchestration.team import run_workspace


async def main() -> None:
    result = await run_workspace("How should Spotify reduce Premium churn?")

    for message in result.messages:
        print(f"\n--- {message.source} ---")
        print(message.content)

    print(f"\n[stopped because: {result.stop_reason}]")


if __name__ == "__main__":
    asyncio.run(main())
