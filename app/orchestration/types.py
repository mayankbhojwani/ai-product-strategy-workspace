# app/orchestration/types.py
from dataclasses import dataclass, field
from typing import Literal, Dict, Any

@dataclass
class AgentResponse:
    agent: str
    label: str
    content: str
    stage: Literal["round_1", "manager_review", "targeted_discussion", "final_decision"]

@dataclass
class WorkspaceEvent:
    type: Literal["stage", "thinking", "message", "done"]
    stage: Literal["round_1", "manager_review", "targeted_discussion", "final_decision"]
    agent: str = ""
    label: str = ""
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
