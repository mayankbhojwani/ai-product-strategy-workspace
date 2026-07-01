"""
Shared agent-construction helpers.

This file exists to avoid repeating AssistantAgent boilerplate
(model client wiring, common kwargs) across all 7 specialist files.
Populated once we implement the Manager Agent and see the actual
duplication, rather than guessing at abstractions up front.
"""
# app/agents/base.py
"""
Shared agent-construction helper.

Every specialist agent is an AssistantAgent that differs only in its name,
description, and system_message. This factory keeps that construction
pattern in one place so agent files stay focused on *what the agent says*,
not *how agents are built*.
"""
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient


def build_agent(
    name: str,
    system_message: str,
    description: str,
    model_client: OpenAIChatCompletionClient,
) -> AssistantAgent:
    """
    Construct a standard AssistantAgent.

    description is distinct from system_message: system_message shapes how
    the agent behaves internally, while description is a short, third-person
    summary AutoGen's team orchestration logic reads to decide things like
    turn order (used starting in the Orchestration step).
    """
    return AssistantAgent(
        name=name,
        model_client=model_client,
        system_message=system_message,
        description=description,
    )
