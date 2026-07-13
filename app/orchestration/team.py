# app/orchestration/team.py
"""
Wires up agent factories and exposes run_workspace() / run_workspace_stream(),
the entry points used by the UI and reporting layer.
"""

from app.config import get_model_client
from app.agents.product_manager import create_product_manager_agent
from app.agents.user_researcher import create_user_researcher_agent
from app.agents.data_scientist import create_data_scientist_agent
from app.agents.growth_lead import create_growth_lead_agent
from app.agents.engineer import create_engineer_agent
from app.agents.devils_advocate import create_devils_advocate_agent
from app.agents.manager import create_manager_agent
from app.orchestration.orchestrator import ProductStrategyOrchestrator

AGENT_FACTORIES = {
    "product_manager": create_product_manager_agent,
    "user_researcher": create_user_researcher_agent,
    "data_scientist": create_data_scientist_agent,
    "growth_lead": create_growth_lead_agent,
    "engineer": create_engineer_agent,
    "devils_advocate": create_devils_advocate_agent,
    "manager": create_manager_agent,
}


def build_orchestrator() -> ProductStrategyOrchestrator:
    client = get_model_client()
    return ProductStrategyOrchestrator(AGENT_FACTORIES, client)


async def run_workspace(problem: str) -> list:
    orchestrator = build_orchestrator()
    return await orchestrator.run_workspace(problem)


async def run_workspace_stream(problem: str):
    orchestrator = build_orchestrator()
    async for event in orchestrator.run_workspace_stream(problem):
        yield event

