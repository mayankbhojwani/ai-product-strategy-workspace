# app/orchestration/workflow.py
from typing import List, Dict

ALL_SPECIALISTS: List[str] = [
    "product_manager",
    "user_researcher",
    "data_scientist",
    "engineer",
    "growth_lead",
    "devils_advocate"
]

AGENT_LABELS: Dict[str, str] = {
    "product_manager": "Product Manager",
    "user_researcher": "User Researcher",
    "data_scientist": "Data Scientist",
    "engineer": "Software Engineer",
    "growth_lead": "Growth Lead",
    "devils_advocate": "Devil's Advocate",
    "manager": "Team Manager"
}

STAGE_LABELS: Dict[str, str] = {
    "round_1": "🔍 Stage 1 — Independent Strategic Analysis",
    "manager_review": "📋 Stage 2 — Cross-Functional Alignment Review",
    "targeted_discussion": "⚖️ Stage 3 — Target Conflict Resolution",
    "final_decision": "🏁 Stage 4 — Final Executive Decision"
}
