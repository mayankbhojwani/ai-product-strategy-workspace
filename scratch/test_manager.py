# scratch/test_manager_rounds.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from app.config import get_model_client  # <-- add this
from app.orchestration.orchestrator import ProductStrategyOrchestrator, AgentResponse
from app.agents.product_manager import create_product_manager_agent
from app.agents.user_researcher import create_user_researcher_agent
from app.agents.data_scientist import create_data_scientist_agent
from app.agents.growth_lead import create_growth_lead_agent
from app.agents.engineer import create_engineer_agent
from app.agents.devils_advocate import create_devils_advocate_agent
from app.agents.manager import create_manager_agent

AGENT_FACTORIES = {
    "product_manager": create_product_manager_agent,
    "user_researcher": create_user_researcher_agent,
    "data_scientist": create_data_scientist_agent,
    "growth_lead": create_growth_lead_agent,
    "engineer": create_engineer_agent,
    "devils_advocate": create_devils_advocate_agent,
    "manager": create_manager_agent,
}

async def main():
    client = get_model_client()         # <-- OpenRouter client
    orch = ProductStrategyOrchestrator(
        AGENT_FACTORIES, client,  # <-- pass it in
    )

    orch.history = [
        AgentResponse("product_manager", "Product Manager", "Proposal A: do X.", "round_1"),
        AgentResponse("growth_lead", "Growth Lead", "Disagree, we should do Y instead.", "round_1"),
    ]

    from app.orchestration.manager_rounds import MANAGER_ROUND_1
    try:
        response = await orch._run_manager("round_1_summary", "Test problem", MANAGER_ROUND_1)
        print("SUCCESS")
        print(repr(response.content))
    except Exception:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
