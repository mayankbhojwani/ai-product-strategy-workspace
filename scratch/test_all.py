# scratch/test_team.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from app.orchestration.team import run_workspace


async def main() -> None:
    result = await run_workspace("How should Spotify reduce Premium churn?")

    for message in result:
        print(f"\n--- {message.label} ({message.stage}) ---")
        print(message.content)



if __name__ == "__main__":
    asyncio.run(main())
