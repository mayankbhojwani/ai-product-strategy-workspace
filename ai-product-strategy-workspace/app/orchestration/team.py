"""
Builds the AutoGen Team (multi-agent execution graph) from the individual
agents, and exposes a single run_workspace(problem: str) entry point
that the UI layer calls. This is the only file that knows how agents
talk to each other.
"""
# app/orchestration/team.py
"""
Composes the 7 agents into a runnable Team and exposes run_workspace(),
the single entry point the UI layer will call. This is the only file
that knows how agents are sequenced or when the conversation ends.
"""

from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_agentchat.base import TaskResult

from app.config import get_model_client
from app.agents.product_manager import create_product_manager_agent
from app.agents.user_researcher import create_user_researcher_agent
from app.agents.data_scientist import create_data_scientist_agent
from app.agents.growth_lead import create_growth_lead_agent
from app.agents.engineer import create_engineer_agent
from app.agents.devils_advocate import create_devils_advocate_agent
from app.agents.manager import create_manager_agent


def build_team() -> RoundRobinGroupChat:
    """
    Builds the team fresh each call. AssistantAgents are stateful across a
    run, so we don't reuse a single team instance across multiple user
    problems -- each call to run_workspace() gets a clean team with no
    memory of a previous, unrelated problem.
    """
    client = get_model_client()

    # Fixed analytical order: generative specialists first, reactive roles
    # next, Manager last to synthesize everyone's contribution.
    agents = [
        create_product_manager_agent(client),
        create_user_researcher_agent(client),
        create_data_scientist_agent(client),
        create_growth_lead_agent(client),
        create_engineer_agent(client),
        create_devils_advocate_agent(client),
        create_manager_agent(client),
    ]

    # Whichever condition fires first ends the conversation:
    # - Manager says TERMINATE as instructed (expected path)
    # - Safety net in case it doesn't (7 agents x 1 turn each, so 7 messages
    #   is exactly one full round -- termination anyway once each has spoken)
    termination = TextMentionTermination("TERMINATE") | MaxMessageTermination(7)

    return RoundRobinGroupChat(agents, termination_condition=termination)


async def run_workspace(problem: str) -> TaskResult:
    """
    Runs the full team on a single product problem and returns the
    complete TaskResult, including every agent's message in order.
    The UI layer calls this and nothing else.
    """
    team = build_team()
    result = await team.run(task=problem)
    return result
