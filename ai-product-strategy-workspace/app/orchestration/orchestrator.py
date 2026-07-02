# app/orchestration/orchestrator.py
"""
Runs the 3-round multi-round discussion defined in workflow.py.

Round 1: every specialist analyzes independently (no cross-visibility).
Manager: summarizes disagreements only -- flags which specialists are
    involved via a machine-readable INVOLVED_AGENTS line.
Round 2: only flagged specialists respond, to defend/refine/challenge --
    no new ideas.
Manager: summarizes what's resolved vs. still uncertain -- flags remaining
    specialists via UNRESOLVED_AGENTS.
Round 3: only flagged specialists propose the smallest next validating step.
Manager: final recommendation with rejected alternatives, risks, next step.
"""

import asyncio
import re
from dataclasses import dataclass
from typing import Any, AsyncIterator, Callable
from app.orchestration.workflow import ALL_SPECIALISTS, ROUND_DESCRIPTIONS, ROUND_LABELS

LABELS = {
    "product_manager": "Product Manager",
    "user_researcher": "User Researcher",
    "engineer": "Software Engineer",
    "data_scientist": "Data Scientist",
    "growth_lead": "Growth Lead",
    "devils_advocate": "Devil's Advocate",
    "manager": "Manager",
}

INVOLVED_PATTERN = re.compile(r"INVOLVED_AGENTS:\s*(.+)", re.IGNORECASE)
UNRESOLVED_PATTERN = re.compile(r"UNRESOLVED_AGENTS:\s*(.+)", re.IGNORECASE)


@dataclass
class AgentResponse:
    agent: str
    label: str
    content: str
    stage: str = ""


def _extract_agent_list(text: str, pattern: re.Pattern) -> tuple[str, list[str], bool]:
    """
    Pulls a machine-readable 'X_AGENTS: a, b, c' line out of the Manager's
    summary. Returns (display_text_without_the_tag, agent_names, was_fallback).

    was_fallback=True means the tag was missing/unparseable and we defaulted
    to including everyone -- safer than silently skipping a round because
    the model didn't follow the format.
    """
    match = pattern.search(text)
    display_text = pattern.sub("", text).strip()

    if not match:
        return display_text, list(ALL_SPECIALISTS), True

    raw = match.group(1).strip()
    if raw.lower().startswith("none"):
        return display_text, [], False

    names = [n.strip().lower().replace(" ", "_") for n in raw.split(",") if n.strip()]
    valid = [n for n in names if n in ALL_SPECIALISTS]

    if not valid:
        return display_text, list(ALL_SPECIALISTS), True
    return display_text, valid, False


async def _call_with_retry(coro_fn: Callable, max_attempts: int = 3, base_delay: float = 20.0):
    """
    Retries a SINGLE agent call on rate-limit errors, with backoff. Applied
    per-call rather than around the whole multi-round run, since this design
    makes far more LLM calls than before -- discarding 15 completed calls
    because call #16 hit a 429 would be wasteful.
    """
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return await coro_fn()
        except Exception as e:
            if "RateLimitError" not in str(e) and "429" not in str(e):
                raise
            last_error = e
            if attempt < max_attempts:
                wait = base_delay * attempt
                print(f"Rate limited, retrying in {wait:.0f}s (attempt {attempt}/{max_attempts})...")
                await asyncio.sleep(wait)
    raise last_error


class ProductStrategyOrchestrator:
    def __init__(self, agent_factories: dict[str, Callable], model_client: Any):
        self.agent_factories = agent_factories
        self.model_client = model_client
        self.history: list[AgentResponse] = []

    async def run_stream(self, problem: str) -> AsyncIterator[dict]:
        self.history.clear()

        # ---- Round 1: independent analysis ----
        async for event in self._run_round("round_1", ALL_SPECIALISTS, problem, independent=True):
            yield event

        # ---- Manager: disagreement summary ----
        summary_1 = await self._run_manager(
            "round_1_summary", problem,
            "This is a DISAGREEMENT SUMMARY, not a final decision. Review the team's "
            "independent analyses above. Identify: (1) key disagreements or conflicting "
            "assumptions between specialists, (2) open questions that need resolving. "
            "Do NOT recommend a final decision yet.\n\n"
            "End your response with exactly one line in this format:\n"
            "INVOLVED_AGENTS: <comma-separated identifiers from: product_manager, "
            "user_researcher, data_scientist, growth_lead, engineer, devils_advocate>\n"
            "List only specialists whose input is needed to resolve a real disagreement. "
            "If there are no real disagreements, write INVOLVED_AGENTS: none",
        )
        display_1, involved, fallback_1 = _extract_agent_list(summary_1.content, INVOLVED_PATTERN)
        summary_1.content = display_1
        yield {"type": "message", "agent": "manager", "label": "Manager",
               "content": display_1, "stage": "round_1_summary"}

        # ---- Round 2: only involved specialists ----
        if involved:
            desc = ROUND_DESCRIPTIONS["round_2"]
            if fallback_1:
                desc += " (Manager didn't specify participants -- including all specialists as a safety fallback.)"
            async for event in self._run_round(
                "round_2", involved, problem, independent=False, description_override=desc,
                round_instruction=(
                    "This is ROUND 2. You are responding because your Round 1 analysis was "
                    "flagged as part of a disagreement. Defend, refine, or challenge your "
                    "previous position based on the disagreement summary above. Do NOT "
                    "propose any completely new product ideas -- focus only on resolving "
                    "the disagreement."
                ),
            ):
                yield event
        else:
            yield {"type": "stage", "stage": "round_2", "label": ROUND_LABELS["round_2"],
                   "description": "No disagreements identified -- Round 2 skipped."}

        # ---- Manager: resolution summary ----
        summary_2 = await self._run_manager(
            "round_2_summary", problem,
            "Summarize what has been RESOLVED in the discussion so far, and what remains "
            "UNCERTAIN. Do not give a final recommendation yet.\n\n"
            "End your response with exactly one line in this format:\n"
            "UNRESOLVED_AGENTS: <comma-separated identifiers from: product_manager, "
            "user_researcher, data_scientist, growth_lead, engineer, devils_advocate>\n"
            "If everything is resolved, write UNRESOLVED_AGENTS: none",
        )
        display_2, unresolved, fallback_2 = _extract_agent_list(summary_2.content, UNRESOLVED_PATTERN)
        summary_2.content = display_2
        yield {"type": "message", "agent": "manager", "label": "Manager",
               "content": display_2, "stage": "round_2_summary"}

        # ---- Round 3: only specialists needed for unresolved issues ----
        if unresolved:
            desc = ROUND_DESCRIPTIONS["round_3"]
            if fallback_2:
                desc += " (Manager didn't specify participants -- including all specialists as a safety fallback.)"
            async for event in self._run_round(
                "round_3", unresolved, problem, independent=False, description_override=desc,
                round_instruction=(
                    "This is ROUND 3, the final round. Recommend the SMALLEST possible "
                    "next validating step from your domain that would resolve the "
                    "remaining uncertainty -- not a new proposal, just the minimal next "
                    "step needed to reach consensus."
                ),
            ):
                yield event
        else:
            yield {"type": "stage", "stage": "round_3", "label": ROUND_LABELS["round_3"],
                   "description": "No unresolved issues -- Round 3 skipped."}

        # ---- Final recommendation ----
        final = await self._run_manager(
            "final", problem,
            "Produce the FINAL recommendation for this product problem, based on the "
            "entire discussion above. Structure your response with exactly these "
            "sections:\n1. Final Recommendation\n2. Why It Was Chosen\n"
            "3. Alternatives Rejected\n4. Remaining Risks\n5. Next Validation Step\n\n"
            "End your response with the word TERMINATE on its own line.",
        )
        yield {"type": "message", "agent": "manager", "label": "Manager",
               "content": final.content, "stage": "final"}

        yield {"type": "done", "history": self.history}

    async def run(self, problem: str) -> dict:
        async for event in self.run_stream(problem):
            if event["type"] == "done":
                return event
        return {"type": "done", "history": self.history}

    async def _run_round(
        self, round_key: str, participants: list[str], problem: str,
        independent: bool = False, round_instruction: str = "",
        description_override: str | None = None,
    ) -> AsyncIterator[dict]:
        yield {
            "type": "stage", "stage": round_key, "label": ROUND_LABELS[round_key],
            "description": description_override or ROUND_DESCRIPTIONS[round_key],
        }
        for agent_name in participants:
            yield {"type": "thinking", "agent": agent_name, "label": LABELS[agent_name]}
            response = await self._run_agent(agent_name, round_key, problem, round_instruction, independent)
            self.history.append(response)
            yield {"type": "message", "agent": response.agent, "label": response.label,
                   "content": response.content, "stage": round_key}

    async def _run_agent(
        self, agent_name: str, round_key: str, original_problem: str,
        round_instruction: str, independent: bool,
    ) -> AgentResponse:
        prompt = self._build_prompt(agent_name, original_problem, round_instruction, independent)
        agent = self.agent_factories[agent_name](self.model_client)

        result = await _call_with_retry(lambda: agent.run(task=prompt))
        assistant_messages = [m for m in result.messages if getattr(m, "source", None) == agent_name]
        if not assistant_messages:
            raise RuntimeError(f"{agent_name} produced no response in {round_key}.")

        return AgentResponse(
            agent=agent_name, label=LABELS[agent_name],
            content=assistant_messages[-1].content, stage=round_key,
        )

    async def _run_manager(self, round_key: str, problem: str, round_instruction: str) -> AgentResponse:
        prompt = self._build_prompt("manager", problem, round_instruction, independent=False)
        agent = self.agent_factories["manager"](self.model_client)

        result = await _call_with_retry(lambda: agent.run(task=prompt))
        assistant_messages = [m for m in result.messages if getattr(m, "source", None) == "manager"]
        if not assistant_messages:
            raise RuntimeError(f"manager produced no response in {round_key}.")

        response = AgentResponse(
            agent="manager", label="Manager",
            content=assistant_messages[-1].content, stage=round_key,
        )
        self.history.append(response)
        return response

    def _build_prompt(
        self, agent_name: str, original_problem: str, round_instruction: str, independent: bool,
    ) -> str:
        text = f"Product Problem:\n\n{original_problem}\n\n"

        if independent:
            # Round 1 only: no history is consulted at all, structurally --
            # not just instructed -- so independence can't leak.
            text += (
                "This is Round 1: give your INDEPENDENT analysis. Other specialists "
                "are analyzing this problem in parallel -- you have no access to "
                "their input and should not assume what they'll say.\n\n"
            )
            return (text + round_instruction).strip()

        if self.history:
            text += "Previous discussion:\n\n"
            for msg in self.history:
                text += f"--- {msg.label} ({msg.stage}) ---\n{msg.content}\n\n"

        if agent_name != "manager":
            already_spoke = any(m.agent == agent_name for m in self.history)
            if already_spoke:
                text += (
                    "\nNote: you already gave an initial response above. Respond "
                    "according to the current round's instruction below -- do not "
                    "just repeat your earlier answer verbatim.\n"
                )

        if round_instruction:
            text += f"\n{round_instruction}\n"

        return text.strip()
