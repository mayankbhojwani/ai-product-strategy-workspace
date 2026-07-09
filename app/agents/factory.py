# app/agents/factory.py
from typing import Dict, Callable, Any
from autogen_agentchat.agents import AssistantAgent
from app.agents.base import build_agent

# Import your existing specialist system message strings and descriptions
from app.agents.manager import SYSTEM_MESSAGE as MGR_SYS, DESCRIPTION as MGR_DESC
from app.agents.product_manager import SYSTEM_MESSAGE as PM_SYS, DESCRIPTION as PM_DESC
from app.agents.user_researcher import SYSTEM_MESSAGE as UR_SYS, DESCRIPTION as UR_DESC
from app.agents.engineer import SYSTEM_MESSAGE as ENG_SYS, DESCRIPTION as ENG_DESC
from app.agents.data_scientist import SYSTEM_MESSAGE as DS_SYS, DESCRIPTION as DS_DESC
from app.agents.growth_lead import SYSTEM_MESSAGE as GL_SYS, DESCRIPTION as GL_DESC
from app.agents.devils_advocate import SYSTEM_MESSAGE as DA_SYS, DESCRIPTION as DA_DESC

agent_factories: Dict[str, Callable[[Any], AssistantAgent]] = {
    "manager": lambda client: build_agent("manager", client, MGR_SYS, MGR_DESC),
    "product_manager": lambda client: build_agent("product_manager", client, PM_SYS, PM_DESC),
    "user_researcher": lambda client: build_agent("user_researcher", client, UR_SYS, UR_DESC),
    "engineer": lambda client: build_agent("engineer", client, ENG_SYS, ENG_DESC),
    "data_scientist": lambda client: build_agent("data_scientist", client, DS_SYS, DS_DESC),
    "growth_lead": lambda client: build_agent("growth_lead", client, GL_SYS, GL_DESC),
    "devils_advocate": lambda client: build_agent("devils_advocate", client, DA_SYS, DA_DESC),
}
