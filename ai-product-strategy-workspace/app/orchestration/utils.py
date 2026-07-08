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

def parse_metadata_block(content: str) -> dict:
    """
    Parses metadata from the agent response block [METADATA]...[/METADATA].
    """
    import re
    meta_pattern = re.compile(r"\[METADATA\](.*?)\[/METADATA\]", re.DOTALL | re.IGNORECASE)
    match = meta_pattern.search(content)
    
    # Default values
    confidence = "Medium"
    assumptions = []
    risks = []
    clean_content = content
    
    if match:
        meta_content = match.group(1)
        # remove the metadata block from the content
        clean_content = content.replace(match.group(0), "").strip()
        
        # parse confidence
        conf_match = re.search(r"CONFIDENCE:\s*(\w+)", meta_content, re.IGNORECASE)
        if conf_match:
            confidence = conf_match.group(1).strip().capitalize()
            if confidence not in ["High", "Medium", "Low"]:
                confidence = "Medium"
                
        # parse assumptions
        ass_match = re.search(r"KEY ASSUMPTIONS:\s*(.*?)(?=RISKS:|$)", meta_content, re.DOTALL | re.IGNORECASE)
        if ass_match:
            ass_text = ass_match.group(1)
            assumptions = [line.strip("- *").strip() for line in ass_text.strip().split("\n") if line.strip()]
            
        # parse risks
        risks_match = re.search(r"RISKS:\s*(.*)", meta_content, re.DOTALL | re.IGNORECASE)
        if risks_match:
            risks_text = risks_match.group(1)
            risks = [line.strip("- *").strip() for line in risks_text.strip().split("\n") if line.strip()]
            
    return {
        "clean_content": clean_content,
        "confidence": confidence,
        "assumptions": assumptions if assumptions else ["None identified"],
        "risks": risks if risks else ["None identified"]
    }

