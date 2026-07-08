# 🧠 AI Product Strategy Workspace (CEO Mode)

An interactive, multi-agent product strategy simulation workspace built on **Microsoft AutoGen (AgentChat API)** and **Streamlit**. 

Instead of generating reports in isolation, this workspace places the human in the loop as the **CEO**, leading an executive committee of AI specialists to tackle complex product problems (e.g. *"How can Spotify reduce Premium churn?"*).

---

## 🧭 Product Architecture: The 6-Phase Workflow

The workspace is structured as a state-machine driven decision workflow:

```
[Phase 1: Intake] ➔ [Phase 2: Debate Loop] ➔ [Phase 3: Decision Points] 
                        └─ (Low-Conf Gates)          │
[Phase 6: Sign-off] ◀── [Phase 4: MoSCoW Backlog] ◄──┘
```

1. **Phase 1 — Strategic Intake**: The Team Manager conducts a 3-question adaptive interview to align target user, business outcomes, and key constraints.
2. **Phase 2 — Executive Debate**: Six AI specialists present their recommendations one by one. The CEO reviews each agent's parsed **Confidence**, **Key Assumptions**, and **Risks**, with options to *Approve*, *Request Reconsideration (with feedback)*, or *Override*.
3. **Phase 3 — Decision Points (Conflict Resolution)**: If the Manager detects opposing views (e.g. Freemium vs. Paid Trial), the workspace pauses and prompts the CEO to select a strategic direction.
4. **Phase 4 — Feature Prioritization**: The PM proposes 5 candidate features based on the selected strategic direction. The CEO prioritizes them using the **MoSCoW framework**.
5. **Phase 5 — Confidence Gates**: If any specialist reports **Low Confidence**, execution pauses until the CEO provides unblocking context (documents, metrics, or notes).
6. **Phase 6 — Final Review & Sign-off**: The CEO reviews and edits the final drafted roadmap sections before exporting a compiled executive PDF report.

---

## 🛠️ Technical Stack & Implementation Details

*   **Agent Orchestration Engine**: Built with **Microsoft AutoGen (AgentChat API)**, wrapping multiple `AssistantAgent` units.
*   **Frontend Interface**: Implemented using **Streamlit** to handle stateful, asynchronous paused-execution loops.
*   **Large Language Model**: Integrated with OpenAI's GPT models via `OpenAIChatCompletionClient`.
*   **PDF Generation Layer**: Utilizes **ReportLab**'s structural Flowables (`SimpleDocTemplate`, `NumberedCanvas`) to build publication-grade PDF documents.
*   **Metadata Parsing**: Built with custom regex extractors in `utils.py` that isolate structured metadata blocks appended to agent outputs:
    ```markdown
    [METADATA]
    CONFIDENCE: High/Medium/Low
    KEY ASSUMPTIONS:
    - [Assumption]
    RISKS:
    - [Risk]
    [/METADATA]
    ```

---

## 🚀 Setup & Execution

### 1. Prerequisites
Ensure you have Python 3.10+ installed and your OpenAI API key ready.

### 2. Installation
Clone the workspace and install the dependencies in a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file:
```env
OPENAI_API_KEY=your-api-key-here
```

### 4. Running the Workspace
Execute the Streamlit application:
```bash
streamlit run app/ui/streamlit_app.py
```
