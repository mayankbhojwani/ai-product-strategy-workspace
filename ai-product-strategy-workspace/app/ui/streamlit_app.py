# app/ui/streamlit_app.py
import asyncio
import tempfile

import streamlit as st

from app.orchestration.team import run_workspace_stream
from app.reporting.pdf_report import generate_pdf_report

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
    Consumes the event stream and updates the UI as each event arrives --
    NOT after collecting them all -- so the "thinking" indicators and
    results actually appear live, which is the whole point of using
    run_workspace_stream() over the blocking run_workspace().
    """
    final_history = None

    async for event in run_workspace_stream(problem_text):
        event_type = event["type"]

        if event_type == "stage":
            stage_placeholder.info(f"### {event['label']}\n\n{event['description']}")

        elif event_type == "thinking":
            thinking_placeholder.write(f"🤖 **{event['label']}** is thinking...")

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
    st.header("Discussion")
    discussion_container = st.container()

    try:
        final_history = asyncio.run(
            run_and_render(problem, stage_placeholder, thinking_placeholder, discussion_container)
        )
    except Exception as e:
        st.error(f"Workspace failed:\n\n{e}")
        st.stop()

    thinking_placeholder.empty()

    if not final_history:
        st.error("The workspace finished without producing any results.")
        st.stop()

    st.success("Analysis Complete!")

    st.divider()
    st.header("Executive Recommendation")

    manager_response = next(
        (r for r in reversed(final_history) if r.agent == "manager"),
        None,
    )

    if manager_response:
        st.markdown(manager_response.content)
    else:
        st.info("No manager recommendation found.")

    pdf_result = {"history": final_history}

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        generate_pdf_report(problem, pdf_result, tmp.name)
        pdf_bytes_path = tmp.name

    with open(pdf_bytes_path, "rb") as f:
        pdf_bytes = f.read()

    st.download_button(
        label="📄 Download PDF Report",
        data=pdf_bytes,
        file_name="product_strategy_report.pdf",
        mime="application/pdf",
    )
