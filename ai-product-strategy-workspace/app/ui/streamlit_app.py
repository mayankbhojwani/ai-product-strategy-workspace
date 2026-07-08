# app/ui/streamlit_app.py
import sys
import os
# Ensure project root is in the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import asyncio
import tempfile
import streamlit as st
import re


# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import dependencies
from autogen_ext.models.openai import OpenAIChatCompletionClient
from app.orchestration.types import AgentResponse
from app.orchestration.workflow import ALL_SPECIALISTS, AGENT_LABELS, STAGE_LABELS
from app.reporting.pdf_report import generate_pdf_report, _extract_section
from app.agents.factory import agent_factories
from app.config import get_model_client
from app.orchestration.utils import parse_metadata_block, call_llm_with_retry

st.set_page_config(
    page_title="AI Product Strategy Workspace",
    page_icon="🧠",
    layout="wide",
)

# Premium UI CSS Styling
st.markdown("""
<style>
    .reportview-container {
        background: #0F172A;
    }
    .card {
        background-color: #1E293B;
        border-radius: 12px;
        padding: 24px;
        border: 1px solid #334155;
        margin-bottom: 20px;
    }
    .badge-high {
        background-color: #059669;
        color: white;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
    }
    .badge-medium {
        background-color: #D97706;
        color: white;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
    }
    .badge-low {
        background-color: #DC2626;
        color: white;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


st.title("🧠 AI Product Strategy Workspace")
st.markdown("🧑‍✈️ **CEO Mode:** Direct your executive team of AI specialists through an interactive strategy planning cycle.")

# Initialize Session State
if "phase" not in st.session_state:
    st.session_state.phase = "intake_input"
if "problem" not in st.session_state:
    st.session_state.problem = ""
if "questions" not in st.session_state:
    st.session_state.questions = []
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "history" not in st.session_state:
    st.session_state.history = []
if "parsed_history" not in st.session_state:
    st.session_state.parsed_history = []
if "agent_idx" not in st.session_state:
    st.session_state.agent_idx = 0
if "user_feedbacks" not in st.session_state:
    st.session_state.user_feedbacks = {}
if "extra_context" not in st.session_state:
    st.session_state.extra_context = ""
if "conflict_data" not in st.session_state:
    st.session_state.conflict_data = {}
if "chosen_direction" not in st.session_state:
    st.session_state.chosen_direction = ""
if "features" not in st.session_state:
    st.session_state.features = []
if "moscow_priorities" not in st.session_state:
    st.session_state.moscow_priorities = {}
if "low_confidence_gate" not in st.session_state:
    st.session_state.low_confidence_gate = None
if "final_drafts" not in st.session_state:
    st.session_state.final_drafts = {}

# Verify API key
if not os.environ.get("OPENAI_API_KEY"):
    st.error("Error: OPENAI_API_KEY is not found in environment. Check your .env file.")
    st.stop()

# Helper: Initialize client
@st.cache_resource
def get_cached_client():
    return get_model_client()

model_client = get_cached_client()

# ==========================================
# PHASE 1: INTAKE INPUT & INTERVIEW
# ==========================================
if st.session_state.phase == "intake_input":
    st.header("Phase 1 — Strategic Intake")
    problem_input = st.text_area(
        "Enter the Product Problem",
        placeholder="Example: How can Spotify reduce Premium churn?",
        height=120,
    )
    if st.button("Generate Interview Questions", use_container_width=True):
        if not problem_input.strip():
            st.error("Please enter a product problem.")
        else:
            st.session_state.problem = problem_input
            # Ask manager to generate clarification questions
            with st.spinner("Team Manager is analyzing the problem statement..."):
                try:
                    manager_agent = agent_factories["manager"](model_client)
                    prompt = f"""You are the Team Manager. The user has proposed a product problem: "{problem_input}".
                    Generate exactly 3 specific, adaptive clarification questions to narrow down the target customer, success metrics, constraints, budget, timeline, or business outcome.
                    Format your output as a simple numbered list, like:
                    1. Question A
                    2. Question B
                    3. Question C
                    Do not include introductory or concluding text.
                    """
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    questions_text = loop.run_until_complete(call_llm_with_retry(manager_agent, prompt))
                    
                    # Simple parse
                    questions = [re.sub(r'^\d+\.\s*', '', q).strip() for q in questions_text.split("\n") if q.strip() and any(char.isdigit() for char in q[:3])]
                    if len(questions) < 3:
                        questions = [
                            "Who is the primary target customer (e.g. B2B vs B2C)?",
                            "What is the definition of success/KPI for this project?",
                            "What is the biggest budget, resource or timeline constraint?"
                        ]
                    st.session_state.questions = questions
                    st.session_state.phase = "intake_interview"
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to generate questions: {e}")

elif st.session_state.phase == "intake_interview":
    st.header("Phase 1 — Executive Intake Interview")
    st.info("The Team Manager requests clarification to ground the upcoming strategic debate:")
    
    st.write(f"**Proposed Problem:** {st.session_state.problem}")
    
    # Form for answers
    answers = {}
    for i, q in enumerate(st.session_state.questions):
        answers[q] = st.text_input(f"Q{i+1}: {q}", key=f"q_input_{i}")
        
    if st.button("Submit Answers & Begin Executive Debate", use_container_width=True):
        st.session_state.answers = answers
        st.session_state.phase = "discussion_loop"
        st.session_state.agent_idx = 0
        st.rerun()

# ==========================================
# PHASE 2 & 5: DISCUSSION LOOP & CONFIDENCE GATES
# ==========================================
elif st.session_state.phase == "discussion_loop":
    st.header("Phase 2 — Executive Team Debate")
    
    # Show sidebar with status
    st.sidebar.markdown("### Executive Team Status")
    for i, agent_id in enumerate(ALL_SPECIALISTS):
        label = AGENT_LABELS[agent_id]
        if i < st.session_state.agent_idx:
            st.sidebar.success(f"✓ {label}")
        elif i == st.session_state.agent_idx:
            st.sidebar.info(f"👉 {label} (Active)")
        else:
            st.sidebar.text(f"  {label} (Pending)")

    agent_id = ALL_SPECIALISTS[st.session_state.agent_idx]
    agent_label = AGENT_LABELS[agent_id]
    
    # Render active discussion history
    with st.expander("Show Prior Discussion Transcript", expanded=False):
        for r in st.session_state.history:
            st.markdown(f"**{r.label}**: {r.content}")
            st.divider()

    # Run agent if we don't have active output in session state
    active_resp_key = f"active_resp_{agent_id}"
    if active_resp_key not in st.session_state:
        with st.spinner(f"{agent_label} is analyzing current context..."):
            try:
                # Build context
                context = f"Product Problem: {st.session_state.problem}\n\n"
                context += "Clarifications from CEO:\n"
                for q, a in st.session_state.answers.items():
                    context += f"- Q: {q}\n  A: {a}\n"
                if st.session_state.extra_context:
                    context += f"- Additional CEO Context: {st.session_state.extra_context}\n"
                    
                context += "\n=== DISCUSSION TRANSCRIPT SO FAR ===\n"
                for r in st.session_state.history:
                    context += f"[{r.label}]: {r.content}\n\n"
                    
                if agent_id in st.session_state.user_feedbacks:
                    context += f"\n=== DIRECT FEEDBACK FOR {agent_label} ===\n"
                    for comment in st.session_state.user_feedbacks[agent_id]:
                        context += f"- {comment}\n"
                
                prompt = f"{context}\n\nPlease provide your analysis and recommendation. Ensure you strictly append the [METADATA] block at the end."
                
                agent_inst = agent_factories[agent_id](model_client)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                raw_text = loop.run_until_complete(call_llm_with_retry(agent_inst, prompt))
                
                parsed = parse_metadata_block(raw_text)
                st.session_state[active_resp_key] = {
                    "raw": raw_text,
                    "clean": parsed["clean_content"],
                    "confidence": parsed["confidence"],
                    "assumptions": parsed["assumptions"],
                    "risks": parsed["risks"]
                }
            except Exception as e:
                st.error(f"Agent failed to execute: {e}")
                st.stop()

    data = st.session_state[active_resp_key]
    
    # Confidence Gate Check (Phase 5)
    if data["confidence"] == "Low" and st.session_state.low_confidence_gate != agent_id:
        st.session_state.low_confidence_gate = agent_id
        
    if st.session_state.low_confidence_gate == agent_id:
        st.warning(f"⚠️ **Confidence Gate Triggered:** {agent_label} reports **Low Confidence** due to missing details.")
        extra_input = st.text_area("Please provide additional context, analytics, target metrics, or constraints to unblock them:", height=100)
        if st.button("Submit Context & Resume", use_container_width=True):
            if extra_input.strip():
                st.session_state.extra_context += f"\n({agent_label} Gate Context): {extra_input}"
                # Remove active response to force regeneration
                del st.session_state[active_resp_key]
                st.session_state.low_confidence_gate = None
                st.rerun()
        st.stop()

    # Display Agent recommendation card
    st.subheader(f"Advisor Recommendation: {agent_label}")
    conf_class = f"badge-{data['confidence'].lower()}"
    st.markdown(f"**Confidence Level:** <span class='{conf_class}'>{data['confidence']}</span>", unsafe_allow_html=True)

    
    st.markdown("### Recommendation")
    st.write(data["clean"])
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Key Assumptions")
        for a in data["assumptions"]:
            st.markdown(f"- {a}")
    with col2:
        st.markdown("### Identified Risks")
        for r in data["risks"]:
            st.markdown(f"- {r}")
            
    st.divider()
    
    # CEO Interventions
    st.subheader("✍️ CEO Intervention Panel")
    comment_input = st.text_area("Provide feedback or corrections to this recommendation (optional):", key=f"fb_{agent_id}")
    
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    with col_btn1:
        if st.button("🟢 Approve Recommendation", use_container_width=True):
            # Save to history
            record = AgentResponse(
                agent=agent_id,
                label=agent_label,
                content=data["raw"],
                stage="round_1"
            )
            st.session_state.history.append(record)
            st.session_state.agent_idx += 1
            if st.session_state.agent_idx >= len(ALL_SPECIALISTS):
                # Transition to Phase 3: Decisions
                st.session_state.phase = "decision_point"
            st.rerun()
            
    with col_btn2:
        if st.button("🔄 Ask Agent to Reconsider", use_container_width=True):
            if not comment_input.strip():
                st.error("Please specify instructions or feedback for the agent to reconsider.")
            else:
                if agent_id not in st.session_state.user_feedbacks:
                    st.session_state.user_feedbacks[agent_id] = []
                st.session_state.user_feedbacks[agent_id].append(comment_input)
                # Delete active response key to trigger reload
                del st.session_state[active_resp_key]
                st.rerun()
                
    with col_btn3:
        if st.button("🔴 Reject & Override", use_container_width=True):
            # Save a custom override note into history
            record = AgentResponse(
                agent=agent_id,
                label=agent_label,
                content=f"**REJECTED BY CEO**. Override Directive: {comment_input if comment_input.strip() else 'No specific rationale provided.'}",
                stage="round_1"
            )
            st.session_state.history.append(record)
            st.session_state.agent_idx += 1
            if st.session_state.agent_idx >= len(ALL_SPECIALISTS):
                st.session_state.phase = "decision_point"
            st.rerun()

# ==========================================
# PHASE 3: DECISION POINTS (CONFLICT RESOLUTION)
# ==========================================
elif st.session_state.phase == "decision_point":
    st.header("Phase 3 — Strategic Alignment & Decision Points")
    st.info("The Team Manager has identified a critical structural conflict among the specialists.")
    
    if not st.session_state.conflict_data:
        with st.spinner("Manager is analyzing consensus and extracting core conflicts..."):
            try:
                manager_agent = agent_factories["manager"](model_client)
                review_builder = [f"Product Problem:\n{st.session_state.problem}\n\n=== SPECIALIST BASELINE RESPONSES ==="]
                for resp in st.session_state.history:
                    review_builder.append(f"--- {resp.label} Response ---\n{resp.content}\n")
                review_builder.append("""You are the Team Manager. Identify a single major strategic fork or conflict from the responses (e.g. business model, target market, or core tech stack).
                Format your response exactly as:
                CONFLICT_TOPIC: <conflict statement>
                OPTION_A: <brief description of Option A>
                OPTION_B: <brief description of Option B>
                """)
                conflict_text = asyncio.run(call_llm_with_retry(manager_agent, "\n".join(review_builder)))
                
                topic_match = re.search(r"CONFLICT_TOPIC:\s*(.*)", conflict_text, re.IGNORECASE)
                a_match = re.search(r"OPTION_A:\s*(.*)", conflict_text, re.IGNORECASE)
                b_match = re.search(r"OPTION_B:\s*(.*)", conflict_text, re.IGNORECASE)
                
                st.session_state.conflict_data = {
                    "topic": topic_match.group(1).strip() if topic_match else "Strategic Direction Fork",
                    "option_a": a_match.group(1).strip() if a_match else "Accelerate feature timeline",
                    "option_b": b_match.group(1).strip() if b_match else "Focus strictly on stabilization"
                }
            except Exception as e:
                st.error(f"Failed to identify decision points: {e}")
                st.stop()
                
    st.markdown(f"### ⚖️ Conflict: {st.session_state.conflict_data['topic']}")
    st.write("Please select the strategic direction to pursue:")
    
    choice = st.radio(
        "Executive Selection",
        options=[
            f"Option A: {st.session_state.conflict_data['option_a']}",
            f"Option B: {st.session_state.conflict_data['option_b']}",
            "Custom Directive (Write below)"
        ]
    )
    
    custom_dir = st.text_input("Custom Strategic Direction:")
    
    if st.button("Confirm Strategic Choice", use_container_width=True):
        if choice == "Custom Directive (Write below)":
            if not custom_dir.strip():
                st.error("Please enter a custom directive.")
                st.stop()
            st.session_state.chosen_direction = custom_dir
        else:
            st.session_state.chosen_direction = choice
            
        st.session_state.phase = "feature_prioritization"
        st.rerun()

# ==========================================
# PHASE 4: FEATURE PRIORITIZATION
# ==========================================
elif st.session_state.phase == "feature_prioritization":
    st.header("Phase 4 — Feature Backlog & MoSCoW Prioritization")
    st.info(f"Based on the chosen strategic direction: **{st.session_state.chosen_direction}**, compile and prioritize candidate features.")
    
    if not st.session_state.features:
        with st.spinner("Generating candidate features..."):
            try:
                pm_agent = agent_factories["product_manager"](model_client)
                prompt = f"""Based on the strategic direction choice: "{st.session_state.chosen_direction}" for problem: "{st.session_state.problem}", generate 5 specific candidate product features.
                Format them strictly as lines starting with feature names, like:
                1. Feature Name: Description
                2. Feature Name: Description
                """
                features_text = asyncio.run(call_llm_with_retry(pm_agent, prompt))
                features = [re.sub(r'^\d+\.\s*', '', f).strip() for f in features_text.split("\n") if f.strip() and ":" in f]
                st.session_state.features = features if features else [
                    "Enhanced onboarding experience: Interactive walk-through",
                    "Predictive churn detection engine: ML metrics parsing",
                    "Customized user recommendation feeds: Tailored dynamic listings",
                    "Localized pricing strategies: Geographically targeted packages",
                    "Offline strategy modes: Local caching sync features"
                ]
            except Exception as e:
                st.error(f"Failed to generate features: {e}")
                st.stop()
                
    st.write("Assign MoSCoW priority levels to each feature:")
    priorities = {}
    for f in st.session_state.features:
        name = f.split(":")[0].strip()
        desc = f.split(":")[1].strip() if ":" in f else ""
        priorities[name] = st.selectbox(
            f"**{name}** — {desc}",
            options=["Must Have", "Should Have", "Could Have", "Won't Have"],
            key=f"moscow_{name}"
        )
        
    if st.button("Lock Prioritization & Generate Final Reports", use_container_width=True):
        st.session_state.moscow_priorities = priorities
        st.session_state.phase = "final_review"
        st.rerun()

# ==========================================
# PHASE 6: FINAL REVIEW
# ==========================================
elif st.session_state.phase == "final_review":
    st.header("Phase 6 — Executive Strategy Consensus Sign-off")
    st.info("Edit the final executive synthesis drafted by your team before exporting the PDF.")
    
    if not st.session_state.final_drafts:
        with st.spinner("Compiling final strategy drafts..."):
            try:
                manager_agent = agent_factories["manager"](model_client)
                recs_desc = ", ".join([f"{k} ({v})" for k, v in st.session_state.moscow_priorities.items()])
                prompt = f"""Compile the final product strategy recommendation based on:
                - Problem: {st.session_state.problem}
                - Selected strategic direction: {st.session_state.chosen_direction}
                - Feature Priority: {recs_desc}
                
                Provide a structured report with exactly these 4 sections:
                
                ### Executive Summary
                <summary>
                
                ### Prioritized Recommendations
                <recommendations>
                
                ### Implementation Roadmap
                <roadmap>
                
                ### Remaining Risks
                <risks>
                """
                drafts_text = asyncio.run(call_llm_with_retry(manager_agent, prompt))
                
                st.session_state.final_drafts = {
                    "Executive Summary": _extract_section(drafts_text, "Executive Summary") or "Executive draft summaries placeholder.",
                    "Prioritized Recommendations": _extract_section(drafts_text, "Prioritized Recommendations") or "Draft recommendations placeholder.",
                    "Implementation Roadmap": _extract_section(drafts_text, "Implementation Roadmap") or "Draft roadmap placeholder.",
                    "Remaining Risks": _extract_section(drafts_text, "Remaining Risks") or "Draft risks placeholder."
                }
            except Exception as e:
                st.error(f"Failed to generate draft: {e}")
                st.stop()
                
    # Show editable fields
    final_exec_summary = st.text_area("Executive Summary", value=st.session_state.final_drafts["Executive Summary"], height=120)
    final_recs = st.text_area("Prioritized Recommendations", value=st.session_state.final_drafts["Prioritized Recommendations"], height=120)
    final_roadmap = st.text_area("Implementation Roadmap", value=st.session_state.final_drafts["Implementation Roadmap"], height=120)
    final_risks = st.text_area("Remaining Risks", value=st.session_state.final_drafts["Remaining Risks"], height=120)
    
    if st.button("Generate Final Report & Download", use_container_width=True):
        # Format final recommendation string
        consensus_text = f"""
        ## Executive Summary
        {final_exec_summary}
        
        ## Final Recommendation
        {final_recs}
        
        ## Next Validation Step
        {final_roadmap}
        
        ## Remaining Risks
        {final_risks}
        """
        
        # Inject manager final response back into the history trace
        final_record = AgentResponse(
            agent="manager",
            label="Team Manager",
            content=consensus_text,
            stage="final_decision"
        )
        # Avoid duplicate final decisions
        history_clean = [r for r in st.session_state.history if r.stage != "final_decision"]
        history_clean.append(final_record)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            generate_pdf_report(
                problem=st.session_state.problem,
                history=history_clean,
                output_path=tmp.name
            )
            pdf_bytes_path = tmp.name
            
        with open(pdf_bytes_path, "rb") as f:
            pdf_bytes = f.read()
            
        st.download_button(
            label="📄 Download Executive Strategy PDF",
            data=pdf_bytes,
            file_name="product_strategy_consensus_report.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        
        if st.button("Start New Strategy Workspace"):
            st.session_state.clear()
            st.rerun()
