#!/usr/bin/env bash
set -e

ROOT="ai-product-strategy-workspace"

# --- Directories ---
mkdir -p "$ROOT"/app/agents
mkdir -p "$ROOT"/app/orchestration
mkdir -p "$ROOT"/app/ui

cd "$ROOT"

# --- app/ ---
cat > app/__init__.py << 'EOF'
"""AI Product Strategy Workspace — multi-agent product analysis built on AutoGen."""
EOF

cat > app/config.py << 'EOF'
"""
Centralized configuration.

Will hold:
- Settings loaded from .env (API keys, base_url for OpenAI/OpenRouter, model name)
- A single factory function that builds the AutoGen model client,
  so every agent file requests a client the same way instead of
  duplicating client-construction logic.
"""
EOF

# --- app/agents/ ---
cat > app/agents/__init__.py << 'EOF'
"""Agent package: one specialist per file, each exposing create_<role>_agent()."""
EOF

cat > app/agents/base.py << 'EOF'
"""
Shared agent-construction helpers.

This file exists to avoid repeating AssistantAgent boilerplate
(model client wiring, common kwargs) across all 7 specialist files.
Populated once we implement the Manager Agent and see the actual
duplication, rather than guessing at abstractions up front.
"""
EOF

cat > app/agents/manager.py << 'EOF'
"""Manager Agent — coordinates the specialist team and writes the final executive summary."""
EOF

cat > app/agents/product_manager.py << 'EOF'
"""Product Manager Agent — frames the problem, prioritizes trade-offs, proposes solutions."""
EOF

cat > app/agents/user_researcher.py << 'EOF'
"""User Researcher Agent — brings qualitative user-behavior and motivation perspective."""
EOF

cat > app/agents/data_scientist.py << 'EOF'
"""Data Scientist Agent — grounds discussion in metrics, hypotheses, and measurement design."""
EOF

cat > app/agents/growth_lead.py << 'EOF'
"""Growth Lead Agent — focuses on acquisition, retention, and growth-loop levers."""
EOF

cat > app/agents/engineer.py << 'EOF'
"""Software Engineer Agent — evaluates technical feasibility and implementation cost."""
EOF

cat > app/agents/devils_advocate.py << 'EOF'
"""Devil's Advocate Agent — stress-tests proposals, surfaces risks and blind spots."""
EOF

# --- app/orchestration/ ---
cat > app/orchestration/__init__.py << 'EOF'
"""Orchestration package: composes agents into a runnable Team."""
EOF

cat > app/orchestration/team.py << 'EOF'
"""
Builds the AutoGen Team (multi-agent execution graph) from the individual
agents, and exposes a single run_workspace(problem: str) entry point
that the UI layer calls. This is the only file that knows how agents
talk to each other.
"""
EOF

# --- app/ui/ ---
touch app/ui/__init__.py

cat > app/ui/streamlit_app.py << 'EOF'
"""Streamlit front end. Calls app.orchestration.team.run_workspace() — nothing else."""
EOF

# --- root files ---
cat > main.py << 'EOF'
"""
Local smoke-test entry point (non-Streamlit).
Lets us verify the agent pipeline from the terminal before wiring up the UI.
"""

if __name__ == "__main__":
    print("Project skeleton OK. Agents not implemented yet.")
EOF

cat > requirements.txt << 'EOF'
autogen-agentchat
autogen-ext[openai]
streamlit
python-dotenv
EOF

cat > .env.example << 'EOF'
# Works with either OpenAI or an OpenRouter-compatible endpoint.
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-4.1
EOF

cat > .gitignore << 'EOF'
.venv/
__pycache__/
*.pyc
.env
EOF

cat > README.md << 'EOF'
# AI Product Strategy Workspace

A multi-agent product-strategy tool built on Microsoft AutoGen (AgentChat API).
A user submits a product problem; a team of specialist agents (Product Manager,
User Researcher, Data Scientist, Growth Lead, Engineer, Devil's Advocate) debates
it, coordinated by a Manager Agent that produces the final executive summary.

Status: project skeleton only — implementation in progress.
EOF

echo "Project structure created in ./$ROOT"
