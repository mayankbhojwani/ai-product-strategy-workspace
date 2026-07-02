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

COMMON_SYSTEM_PROMPT = """
You are part of a collaborative AI product strategy team.

General collaboration rules:

1. Carefully read everything previous agents have written.
2. Before giving your own opinion, explicitly reference at least one teammate.
3. Either:
   - agree and extend their idea,
   - disagree and explain why,
   - or suggest a modification.
4. Never simply repeat earlier points.
5. Stay within your area of expertise while helping the team reach the best decision.
6. If another agent makes an assumption, feel free to question it.
7. Keep your response concise and actionable.


## Specific guidance for all agents:
Do not invent statistics, percentages, benchmarks, survey results,
latencies, user counts, API capabilities, or engineering metrics.

If evidence is unavailable, explicitly state that the claim is:

- Hypothesis
- Assumption
- Target metric
- Unknown

Never fabricate precision.
"""

def build_agent(
    name: str,
    model_client,
    system_message: str,
    description: str,
):
    return AssistantAgent(
        name=name,
        model_client=model_client,
        description=description,
        system_message=f"""{COMMON_SYSTEM_PROMPT}

Role-specific instructions:

{system_message}
""",
    )
