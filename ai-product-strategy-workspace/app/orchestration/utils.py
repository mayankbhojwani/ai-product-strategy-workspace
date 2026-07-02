# app/orchestration/utils.py
import re
import asyncio
from typing import List, Tuple, Callable, Any
from app.orchestration.workflow import ALL_SPECIALISTS

INVOLVED_PATTERN = re.compile(r"INVOLVED_AGENTS:\s*(.+)", re.IGNORECASE)

def extract_involved_agents(manager_text: str) -> List[str]:
    """
    Parses the manager output to identify which agents need to engage.
    Falls back to all specialists if the block is missing or malformed.
    """
    match = INVOLVED_PATTERN.search(manager_text)
    if not match:
        return ALL_SPECIALISTS.copy()

    raw_list = match.group(1).strip().lower()
    if "none" in raw_list:
        return []

    extracted = [agent for agent in ALL_SPECIALISTS if agent in raw_list]
    return extracted if extracted else ALL_SPECIALISTS.copy()

async def call_llm_with_retry(agent_instance: Any, prompt: str, max_retries: int = 3, initial_delay: float = 2.0) -> str:
    """
    Resilient execution utility wrap for agent execution calls.
    """
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            # Assumes underlying agent interface exposes a .run() or .generate()
            result = await agent_instance.run(task=prompt)

            # Autogen specific message object resolution
            if hasattr(result, "messages") and result.messages:
                return result.messages[-1].content
            elif isinstance(result, str):
                return result
            return str(result)
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            await asyncio.sleep(delay)
            delay *= 2
    return ""
