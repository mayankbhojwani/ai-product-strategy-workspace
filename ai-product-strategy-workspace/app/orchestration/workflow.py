# app/orchestration/workflow.py
"""
Defines the round structure for the multi-round discussion.

Round 1's participants are fixed and known upfront. Round 2 and Round 3
participants are NOT defined here -- they're determined at runtime by which
specialists the Manager flags as involved in unresolved disagreements. That's
the entire point of this design: debate only where there's real disagreement.
"""

ALL_SPECIALISTS = [
    "product_manager",
    "user_researcher",
    "data_scientist",
    "growth_lead",
    "engineer",
    "devils_advocate",
]

ROUND_LABELS = {
    "round_1": "🔍 Round 1 — Independent Analysis",
    "round_1_summary": "📋 Disagreement Summary",
    "round_2": "⚖️ Round 2 — Resolving Disagreements",
    "round_2_summary": "📋 Resolution Summary",
    "round_3": "🎯 Round 3 — Final Validation Steps",
    "final": "🏁 Final Recommendation",
}

ROUND_DESCRIPTIONS = {
    "round_1": "Each specialist gives an independent analysis, with no visibility into each other's responses.",
    "round_1_summary": "The Manager identifies key disagreements, assumptions, and open questions -- no decision yet.",
    "round_2": "Only specialists involved in a disagreement respond, to defend, refine, or challenge their position.",
    "round_2_summary": "The Manager summarizes what's been resolved and what remains uncertain.",
    "round_3": "Only specialists needed for unresolved issues propose the smallest next step to reach consensus.",
    "final": "The Manager produces the final recommendation, alternatives rejected, risks, and next validation step.",
}
