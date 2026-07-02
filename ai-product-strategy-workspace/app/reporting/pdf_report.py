# app/reporting/pdf_report.py
"""
Generates a PDF report from a completed product strategy discussion.

Consumes the orchestrator's output (list[AgentResponse] wrapped in
{"history": [...]}) rather than AutoGen's TaskResult, since orchestration
was rewritten to a custom multi-stage orchestrator in team.py / orchestrator.py.
"""

import html
import re
from collections import defaultdict
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

REPORT_ORDER = [
    ("manager", "Executive Summary"),
    ("product_manager", "Product Manager"),
    ("user_researcher", "User Researcher"),
    ("engineer", "Software Engineer"),
    ("data_scientist", "Data Scientist"),
    ("growth_lead", "Growth Lead"),
    ("devils_advocate", "Devil's Advocate"),
]


def _strip_terminate(text: str) -> str:
    return re.sub(r"\n?TERMINATE\s*$", "", text, flags=re.MULTILINE).strip()


def _format_content(text: str) -> str:
    text = html.escape(text)

    text = re.sub(r"^### (.+)$", r"<font size=12><b>\1</b></font>", text, flags=re.MULTILINE)
    text = re.sub(r"^## (.+)$", r"<font size=14><b>\1</b></font>", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"^- (.+)$", r"• \1", text, flags=re.MULTILINE)

    return text.replace("\n", "<br/>")


def _page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.grey)
    canvas.drawRightString(7.8 * inch, 0.45 * inch, f"Page {doc.page}")
    canvas.restoreState()


def generate_pdf_report(problem: str, result: dict, output_path: str) -> str:
    """
    Parameters
    ----------
    problem : str
        Original product problem.
    result : dict
        {"history": list[AgentResponse]} -- AgentResponse has .agent, .label,
        .content, .stage. A role (e.g. product_manager) may appear more than
        once across different stages; those entries are merged into one
        section, each labeled with its originating stage so a reader can
        tell Discovery apart from Revision.
    output_path : str
        Destination PDF path.
    """
    history = result.get("history", [])

    # Group by agent, but keep each entry's stage label attached instead of
    # flattening straight to strings -- otherwise a role that speaks twice
    # (Product Manager: Discovery + Revision) becomes unreadable, since you
    # can't tell where one turn ends and the revised one begins.
    messages_by_agent: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for response in history:
        messages_by_agent[response.agent].append((response.stage, response.content))

    styles = getSampleStyleSheet()
    heading_style = ParagraphStyle("Heading", parent=styles["Heading2"], spaceBefore=18, spaceAfter=8)
    sub_heading_style = ParagraphStyle("SubHeading", parent=styles["Heading3"], spaceBefore=12, spaceAfter=5)
    stage_tag_style = ParagraphStyle(
        "StageTag", parent=styles["Normal"], fontSize=9, textColor=colors.grey,
        spaceBefore=2, spaceAfter=2,
    )
    body_style = ParagraphStyle("Body", parent=styles["Normal"], leading=16, spaceAfter=10)
    meta_style = ParagraphStyle("Meta", parent=styles["Normal"], fontSize=9, textColor=colors.grey)

    doc = SimpleDocTemplate(
        output_path, pagesize=letter,
        topMargin=0.75 * inch, bottomMargin=0.75 * inch,
        leftMargin=0.9 * inch, rightMargin=0.9 * inch,
    )

    story = []

    # -- Header --
    story.append(Paragraph("AI Product Strategy Report", styles["Title"]))
    story.append(Paragraph(datetime.now().strftime("Generated %B %d, %Y at %H:%M"), meta_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>Problem Statement</b>", heading_style))
    story.append(Paragraph(_format_content(problem), body_style))
    story.append(HRFlowable(width="100%", color=colors.lightgrey))
    story.append(Spacer(1, 10))

    # -- Executive Summary --
    manager_entries = messages_by_agent.get("manager", [])
    if manager_entries:
        story.append(Paragraph("Executive Summary", heading_style))
        combined = "\n\n".join(content for _, content in manager_entries)
        story.append(Paragraph(_format_content(_strip_terminate(combined)), body_style))
        story.append(HRFlowable(width="100%", color=colors.lightgrey))
        story.append(Spacer(1, 10))

    # -- Team Discussion --
    story.append(Paragraph("Team Deliberation", heading_style))

    for agent, title in REPORT_ORDER[1:]:
        entries = messages_by_agent.get(agent)
        if not entries:
            continue

        story.append(Paragraph(title, sub_heading_style))

        for stage, content in entries:
            # Only show a stage tag when a role appears more than once --
            # a single-turn role (e.g. Data Scientist) doesn't need the noise.
            if len(entries) > 1 and stage:
                story.append(Paragraph(f"<i>{html.escape(stage)}</i>", stage_tag_style))
            story.append(Paragraph(_format_content(content), body_style))

        story.append(HRFlowable(width="80%", color=colors.whitesmoke))
        story.append(Spacer(1, 8))

    doc.build(story, onFirstPage=_page_number, onLaterPages=_page_number)
    return output_path
