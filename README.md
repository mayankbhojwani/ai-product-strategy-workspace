# 🧠 AI Product Strategy Workspace (CEO Mode)
A multi-agent AI workspace that simulates how cross-functional product teams collaborate to solve product strategy problems with a human in the loop.

## Overview
AI Product Strategy Workspace is a multi-agent decision-making system that transforms an open-ended product problem into an executive-ready strategy report.

Instead of relying on a single LLM response, the system assigns distinct responsibilities to multiple AI specialists. The human sits in the loop as the **CEO** to lead, guide, and intervene at every key decision point, while the AI agents act as specialized executives.

A Team Manager coordinates the debate rounds, detects conflicts, and drafts final recommendations, but the human CEO holds final authority to approve, edit, reject, and prioritize directives before any reports are generated.

## Motivation
Large Language Models are excellent at generating answers but often struggle to expose why a particular recommendation was chosen.

Real product decisions are rarely made by a single person—they emerge through discussions and healthy debate between Product Managers, Engineers, Researchers, Growth teams, and Data Scientists.

This project simulates that collaborative process, asking:
*"How would an entire product team reason through this problem, and how can a leader guide them to the right decision?"*

## Features
- **Human-in-the-Loop Interaction (CEO Mode)**: Make strategic decisions at every checkpoint.
- **Multi-Agent Architecture**: 7 specialized agents with distinct mandates.
- **Adaptive Clarification (Intake Interview)**: Dynamic 3-question intake phase to gather target audience, constraints, and success criteria.
- **Parsed Recommendation Blocks**: Clear view of each specialist's recommendation along with parsed **Confidence**, **Key Assumptions**, and **Risks**.
- **CEO Override & Reconsideration Panel**: Provide direct feedback to force an agent to reconsider, or override and inject custom directives.
- **Conflict Resolution (Decision Points)**: Automatic pauses when the Manager detects a disagreement to let the CEO select the strategic direction.
- **Feature Prioritization (MoSCoW Framework)**: Drag and bucket features into Must, Should, Could, or Won't Have lists.
- **Confidence Gates**: Pauses execution to request details (interview notes, documents, or data) if an agent's confidence drops to "Low".
- **Editable Draft Synthesis**: Edit final drafts of the report sections (Executive Summary, Recommendations, Roadmap, Risks) before compiling.
- **Professional PDF Generation**: Generates clean, publication-ready PDF summaries of the strategy report.

## Demo Workflow

```
       [User Product Problem]
                 │
                 ▼
     [Phase 1: Intake Interview] (3 Adaptive Questions)
                 │
                 ▼
     [Phase 2: Specialist Debate] (Pauses for CEO Review/Feedback)
      ├─ Product Manager  ├─ Software Engineer
      ├─ User Researcher  ├─ Growth Lead
      └─ Data Scientist   └─ Devil's Advocate
                 │
                 ▼ (If Confidence is Low ➔ Phase 5: Confidence Gate)
     [Phase 3: Decision Points] (Pauses for CEO to resolve conflicts)
                 │
                 ▼
     [Phase 4: MoSCoW Prioritization] (CEO categorizes features)
                 │
                 ▼
     [Phase 6: Final Review & Sign-Off] (CEO edits final section drafts)
                 │
                 ▼
     [Compiled PDF Report Download]
```

## Multi-Agent Architecture
The workspace consists of seven specialized AI agents:

- **Product Manager (`product_manager`)**: Responsible for problem framing, product strategy, user value, and backlog features.
- **User Researcher (`user_researcher`)**: Responsible for user segmentation, pain points, mental models, and customer assumptions.
- **Data Scientist (`data_scientist`)**: Responsible for North Star metrics, instrumentation, experiment design, and validation metrics.
- **Software Engineer (`engineer`)**: Responsible for feasibility, complexity, dependencies, MVP recommendations, and technical risks.
- **Growth Lead (`growth_lead`)**: Responsible for growth strategy, user incentives, retention, and business impact.
- **Devil's Advocate (`devils_advocate`)**: Responsible for challenging assumptions, stress-testing proposals, and identifying blind spots.
- **Team Manager (`manager`)**: Responsible for coordinating discussions, asking clarification questions, framing strategic conflicts, and drafting recommendations.

## Technology Stack
- **Python**: Core application runtime
- **AutoGen**: Multi-agent orchestration (AgentChat API)
- **Streamlit**: User Interface with premium custom glassmorphic styling
- **ReportLab**: Dynamic PDF report compilation
- **OpenAI-compatible LLM**: Agent reasoning

## Project Structure
```
app/
├── agents/
│   ├── base.py
│   ├── data_scientist.py
│   ├── devils_advocate.py
│   ├── engineer.py
│   ├── factory.py
│   ├── growth_lead.py
│   ├── manager.py
│   ├── product_manager.py
│   └── user_researcher.py
│
├── orchestration/
│   ├── manager_rounds.py
│   ├── orchestrator.py
│   ├── round_prompts.py
│   ├── team.py
│   ├── types.py
│   ├── utils.py
│   └── workflow.py
│
├── reporting/
│   └── pdf_report.py
│
├── ui/
│   └── streamlit_app.py
│
└── config.py
```

## Installation & Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ai-product-strategy-workspace.git
   cd ai-product-strategy-workspace
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   ```

3. **Activate the environment**
   * macOS/Linux:
     ```bash
     source .venv/bin/activate
     ```
   * Windows:
     ```cmd
     .venv\Scripts\activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure Environment Variables**
   Create a `.env` file in the subdirectory `ai-product-strategy-workspace/`:
   ```env
   OPENAI_API_KEY=your-api-key-here
   ```

6. **Run the application**
   ```bash
   streamlit run app/ui/streamlit_app.py
   ```

## Example Product Questions
- How should Spotify improve music discovery?
- Should Netflix introduce an annual subscription?
- How can Airbnb reduce host cancellations?
- How should Duolingo increase user retention?
- Swiggy: decline in repeat orders from college students.

## Current Limitations
- Agent reasoning depends on LLM outputs
- No external web search or live RAG integrations
- Recommendations should be treated as decision support rather than absolute truth
- Session data is not persisted across browser refreshes

## License
This project is licensed under the MIT License.
