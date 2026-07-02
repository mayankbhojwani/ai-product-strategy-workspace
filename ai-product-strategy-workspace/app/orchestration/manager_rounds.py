MANAGER_REVIEW_PROMPT = """
CURRENT TASK

This is the first manager intervention.

Your responsibility is to facilitate the discussion, NOT make a decision.

Review every specialist's response and identify only the disagreements that
materially affect the final product recommendation.

For each disagreement provide:

## Disagreement

- Topic
- Specialists involved
- Position A (1-2 sentences)
- Position B (1-2 sentences)
- Why the disagreement matters

Then identify:

## Competing Hypotheses

List the major hypotheses the team currently holds.

For each hypothesis state whether it is:

- Well Supported
- Partially Supported
- Weakly Supported

Then identify:

## Missing Evidence

List the evidence or validation required before the disagreement can be
resolved.

Rules:

- Do NOT decide who is correct.
- Do NOT recommend a solution.
- Ignore minor disagreements.
- Focus only on issues that materially change the team's direction.
- Base everything only on the discussion.

End your response with EXACTLY one line:

INVOLVED_AGENTS:
<comma-separated identifiers from:
product_manager,
user_researcher,
data_scientist,
growth_lead,
engineer,
devils_advocate>

Include ONLY specialists needed for Round 2.

If no discussion is required write:

INVOLVED_AGENTS: none

KEEP YOUR RESPONSE UNDER 140 WORDS.
"""



MANAGER_FINAL_PROMPT = """
CURRENT TASK

This is the FINAL decision.

Produce an executive recommendation based ONLY on the specialists'
discussion.

Do NOT introduce new ideas.

Do NOT repeat the discussion chronologically.

Do NOT include intermediate disagreement summaries.

Base every conclusion only on what specialists actually argued.

If evidence is weak, explicitly describe it as a:

- Hypothesis
- Assumption
- Validation Goal

Never present unsupported claims as facts.

Use the following structure exactly.

## Executive Summary

Summarize the problem and final recommendation in one concise paragraph.

## Why This Decision

Explain why this recommendation was chosen.

Reference specialist viewpoints where appropriate.

## Alternatives Rejected

For each rejected recommendation explain why it was not prioritized.

## Remaining Risks

List only unresolved risks that materially affect implementation.

## Next Validation Step

Recommend the single highest-priority experiment or validation activity before
additional investment.

## Final Recommendation

Provide a concise executive recommendation balancing:

- user value
- business impact
- engineering feasibility
- implementation risk

Keep the response under 350 words.

End with exactly:

TERMINATE
"""
