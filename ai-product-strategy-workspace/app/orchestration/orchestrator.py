# app/orchestration/orchestrator.py
import asyncio
from typing import AsyncIterator, Dict, Any, Callable, List

from app.orchestration.types import AgentResponse
from app.orchestration.workflow import ALL_SPECIALISTS, AGENT_LABELS, STAGE_LABELS
from app.orchestration.round_prompts import ROUND_1_INSTRUCTION, ROUND_3_INSTRUCTION
from app.orchestration.manager_rounds import MANAGER_REVIEW_PROMPT, MANAGER_FINAL_PROMPT
from app.orchestration.utils import extract_involved_agents, call_llm_with_retry

class ProductStrategyOrchestrator:
    def __init__(self, agent_factories: Dict[str, Callable[[Any], Any]], model_client: Any):
        self.agent_factories = agent_factories
        self.model_client = model_client
        self.history: List[AgentResponse] = []

    async def run_workspace_stream(self, problem: str) -> AsyncIterator[Dict[str, Any]]:
        self.history.clear()

        # ==========================================
        # STAGE 1: INDEPENDENT ANALYSIS
        # ==========================================
        current_stage = "round_1"
        yield self._make_event("stage", current_stage, content=STAGE_LABELS[current_stage])

        for agent_id in ALL_SPECIALISTS:
            yield self._make_event("thinking", current_stage, agent=agent_id, label=AGENT_LABELS[agent_id])

            prompt = f"Product Problem under review:\n{problem}\n\n{ROUND_1_INSTRUCTION}"
            agent_instance = self.agent_factories[agent_id](self.model_client)
            response_text = await call_llm_with_retry(agent_instance, prompt)

            record = AgentResponse(agent=agent_id, label=AGENT_LABELS[agent_id], content=response_text, stage=current_stage)
            self.history.append(record)
            yield self._make_event("message", current_stage, agent=agent_id, label=AGENT_LABELS[agent_id], content=response_text)

        # ==========================================
        # STAGE 2: MANAGER REVIEW
        # ==========================================
        current_stage = "manager_review"
        yield self._make_event("stage", current_stage, content=STAGE_LABELS[current_stage])
        yield self._make_event("thinking", current_stage, agent="manager", label=AGENT_LABELS["manager"])

        review_builder = [f"Product Problem:\n{problem}\n\n=== SPECIALIST BASELINE RESPONSES ==="]
        for resp in [r for r in self.history if r.stage == "round_1"]:
            review_builder.append(f"--- {resp.label} Response ---\n{resp.content}\n")
        review_builder.append(MANAGER_REVIEW_PROMPT)

        manager_agent = self.agent_factories["manager"](self.model_client)
        manager_review_text = await call_llm_with_retry(manager_agent, "\n".join(review_builder))

        involved_agents = extract_involved_agents(manager_review_text)

        record = AgentResponse(agent="manager", label=AGENT_LABELS["manager"], content=manager_review_text, stage=current_stage)
        self.history.append(record)
        yield self._make_event("message", current_stage, agent="manager", label=AGENT_LABELS["manager"], content=manager_review_text)

        # ==========================================
        # STAGE 3: TARGETED DISCUSSION
        # ==========================================
        current_stage = "targeted_discussion"
        if len(involved_agents) > 0:
            yield self._make_event("stage", current_stage, content=STAGE_LABELS[current_stage])

            for agent_id in involved_agents:
                yield self._make_event("thinking", current_stage, agent=agent_id, label=AGENT_LABELS[agent_id])

                prior_baseline = next((r.content for r in self.history if r.agent == agent_id and r.stage == "round_1"), "")
                targeted_prompt = (
                    f"Product Problem:\n{problem}\n\n"
                    f"=== YOUR PREVIOUS BASELINE RESPONSE ===\n{prior_baseline}\n\n"
                    f"=== MANAGER ALIGNMENT REVIEW ===\n{manager_review_text}\n\n"
                    f"{ROUND_3_INSTRUCTION}"
                )

                agent_instance = self.agent_factories[agent_id](self.model_client)
                response_text = await call_llm_with_retry(agent_instance, targeted_prompt)

                record = AgentResponse(agent=agent_id, label=AGENT_LABELS[agent_id], content=response_text, stage=current_stage)
                self.history.append(record)
                yield self._make_event("message", current_stage, agent=agent_id, label=AGENT_LABELS[agent_id], content=response_text)
        else:
            yield self._make_event("stage", current_stage, content="⚖️ Stage 3 — Skipped (No structural alignment updates required)")

        # ==========================================
        # STAGE 4: FINAL EXECUTIVE DECISION
        # ==========================================
        current_stage = "final_decision"
        yield self._make_event("stage", current_stage, content=STAGE_LABELS[current_stage])
        yield self._make_event("thinking", current_stage, agent="manager", label=AGENT_LABELS["manager"])

        final_builder = [f"Product Problem:\n{problem}\n\n=== COMPLETE DESIGN ROUNDS HISTORY ==="]
        for resp in self.history:
            final_builder.append(f"Stage: {resp.stage} | Role: {resp.label}\nResponse:\n{resp.content}\n{'='*20}")
        final_builder.append(MANAGER_FINAL_PROMPT)

        manager_agent = self.agent_factories["manager"](self.model_client)
        final_decision_text = await call_llm_with_retry(manager_agent, "\n".join(final_builder))

        record = AgentResponse(agent="manager", label=AGENT_LABELS["manager"], content=final_decision_text, stage=current_stage)
        self.history.append(record)

        yield self._make_event("message", current_stage, agent="manager", label=AGENT_LABELS["manager"], content=final_decision_text)
        yield {"type": "done", "stage": current_stage, "history": self.history}

    async def run_workspace(self, problem: str) -> List[AgentResponse]:
        async for event in self.run_workspace_stream(problem):
            if event["type"] == "done":
                return self.history
        return self.history

    def _make_event(self, event_type: str, stage: str, agent: str = "", label: str = "", content: str = "") -> Dict[str, Any]:
        return {"type": event_type, "stage": stage, "agent": agent, "label": label, "content": content}
