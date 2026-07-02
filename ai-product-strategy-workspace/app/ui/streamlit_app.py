# app/ui/streamlit_app.py
import os
import asyncio
import tempfile
import streamlit as st

# 1. ADD THIS AT THE ABSOLUTE TOP TO LOAD YOUR .ENV FILE
from dotenv import load_dotenv
load_dotenv()  # This populates os.environ with the variables from your .env file

# Import the V2 client from the extension framework as used in your base.py
from autogen_ext.models.openai import OpenAIChatCompletionClient

# Import the new workspace orchestrator class and the PDF generator layer
from app.orchestration.orchestrator import ProductStrategyOrchestrator
from app.reporting.pdf_report import generate_pdf_report
from app.agents.factory import agent_factories
from app.config import get_model_client
st.set_page_config(
    page_title="AI Product Strategy Workspace",
    page_icon="🧠",
    layout="wide",
)

st.title("🧠 AI Product Strategy Workspace")
st.markdown("Describe a product problem and let an AI product team collaborate on it.")

problem = st.text_area(
    "Product Problem",
    placeholder="Example: How should Spotify reduce Premium churn?",
    height=140,
)

run_button = st.button("Analyze", use_container_width=True)


async def run_and_render(problem_text: str, stage_placeholder, thinking_placeholder, discussion_container):
    """
    Consumes the V2 event stream and updates the UI layout components live
    as each strategic alignment slice finishes executing.
    """
    final_history = None

    # Verify that the environment variable was successfully loaded
    if not os.environ.get("OPENAI_API_KEY"):
        st.error("Error: OPENAI_API_KEY is still not found in your environment. Check your .env file format.")
        st.stop()

    # Initialize the OpenAIChatCompletionClient correctly as required by autogen-ext.
    model_client = get_model_client()

    # Initialize the Orchestration Runner Engine
    orchestrator = ProductStrategyOrchestrator(
        agent_factories=agent_factories,
        model_client=model_client
    )

    async for event in orchestrator.run_workspace_stream(problem_text):
        event_type = event["type"]

        if event_type == "stage":
            stage_text = event.get("content") or event.get("label", "Processing Step")
            stage_placeholder.info(f"### {stage_text}")

        elif event_type == "thinking":
            thinking_placeholder.write(f"🤖 **{event['label']}** is analyzing...")

        elif event_type == "message":
            thinking_placeholder.empty()
            with discussion_container.expander(f"🧑 {event['label']}", expanded=False):
                st.markdown(event["content"])

        elif event_type == "done":
            final_history = event["history"]

    return final_history


if run_button:
    if not problem.strip():
        st.error("Please enter a product problem.")
        st.stop()

    stage_placeholder = st.empty()
    thinking_placeholder = st.empty()

    st.divider()
    st.header("Discussion Log")
    discussion_container = st.container()

    try:
        final_history = asyncio.run(
            run_and_render(problem, stage_placeholder, thinking_placeholder, discussion_container)
        )
    except Exception as e:
        st.error(f"Workspace execution failed:\n\n{e}")
        st.stop()

    thinking_placeholder.empty()

    if not final_history:
        st.error("The workspace finished without producing any structural history assets.")
        st.stop()

    st.success("Analysis Complete!")

    st.divider()
    st.header("Executive Recommendation")

    manager_response = next(
        (r for r in reversed(final_history) if r.agent == "manager" and r.stage == "final_decision"),
        None,
    )

    if manager_response:
        st.markdown(manager_response.content)
    else:
        st.info("No final executive manager decision was found in workspace logs.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        generate_pdf_report(
            problem=problem,
            history=final_history,
            output_path=tmp.name
        )
        pdf_bytes_path = tmp.name

    with open(pdf_bytes_path, "rb") as f:
        pdf_bytes = f.read()

    st.download_button(
        label="📄 Download Executive PDF Report",
        data=pdf_bytes,
        file_name="product_strategy_report.pdf",
        mime="application/pdf",
        use_container_width=True
    )
