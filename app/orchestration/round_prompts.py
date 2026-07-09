ROUND_1_INSTRUCTION = """
CURRENT TASK

This is the FIRST discussion round.

Your objective is to independently analyze the product problem from your area
of expertise.

Approach this as if you are the first specialist in the room.

Guidelines:

- Think independently.
- Do NOT assume previous specialists are correct.
- Do NOT anticipate future criticism.
- Focus only on your own expertise.
- Make the strongest recommendation you can based on the available information.
- Clearly identify assumptions instead of treating them as facts.
- If information is missing, explicitly state what you would need rather than inventing details.
- Prefer solving root causes over symptoms.
- Recommend the smallest meaningful improvement rather than multiple unrelated ideas.

Your response should establish your position clearly so that later specialists
can evaluate, challenge, or build upon it.
"""

ROUND_3_INSTRUCTION = """
CURRENT TASK

You are participating in Round 2 because the Manager identified a discussion
that requires your expertise.

Your goal is NOT to rewrite your previous response.

Your goal is to improve the team's collective decision by responding directly
to the disagreement identified by the Manager.

Before responding:

1. Review the Manager's summary carefully.
2. Review the relevant specialist responses.
3. Decide whether your original reasoning still holds.

Your response should do ONE of the following:

- Defend your position using stronger reasoning.
- Revise your position if another specialist presented better reasoning.
- Partially modify your recommendation to incorporate another specialist's insight.
- Challenge another specialist's assumption with reasoning from your own expertise(only if it is a critical flaw that materially affects the decision).

When responding:

- Explicitly identify which specialist or assumption you are responding to.
- Explain WHY you agree or disagree.
- Stay strictly within your area of expertise and speak from the point of view of your role.
- Do NOT repeat your entire previous recommendation.
- Do NOT introduce completely new product ideas.
- Focus only on resolving the identified disagreement.

If your recommendation changes:

- Clearly explain what changed your thinking.

If your recommendation does NOT change:

- Explain why your original reasoning remains stronger.

Your objective is to move the discussion toward a better decision, not to win
the argument.
"""


