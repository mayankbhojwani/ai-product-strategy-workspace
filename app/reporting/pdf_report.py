# app/reporting/pdf_generator.py
import os
import re
import html
from typing import List, Dict, Any
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, PageBreak, KeepTogether
from reportlab.pdfgen import canvas

from app.orchestration.types import AgentResponse

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas renderer tracking running headers and total page counts dynamically.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages: int):
        self.saveState()
        # Do not draw background running layout grids on Cover Page
        if self._pageNumber == 1:
            self.restoreState()
            return

        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        # Running Top Header
        self.drawString(54, 11 * inch - 36, "AI Product Strategy Workspace — Executive Report")
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, 11 * inch - 42, 8.5 * inch - 54, 11 * inch - 42)

        # Running Bottom Footer
        page_str = f"Page {self._pageNumber} of {total_pages}"
        self.drawRightString(8.5 * inch - 54, 36, page_str)
        self.restoreState()


def _clean_markdown_to_xml(text: str) -> str:
    """
    Escapes characters safely and transforms basic Markdown elements into ReportLab XML markup strings.
    """
    # Strip pseudo-HTML wrapper tags
    text = re.sub(r"</?(summary|recommendations|roadmap|risks|metadata)>", "", text, flags=re.IGNORECASE)

    text = html.escape(text)

    # Machine string cleanups
    text = re.sub(r"TERMINATE\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"INVOLVED_AGENTS:\s*.+$", "", text, flags=re.MULTILINE | re.IGNORECASE)

    # Formatting Conversions
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.*?)\*", r"<i>\1</i>", text)
    text = re.sub(r"^- (.*?)$", r"• \1", text, flags=re.MULTILINE)

    return text.replace("\n", "<br/>")


def _extract_section(text: str, heading_title: str) -> str:
    """
    Extracts structural markdown content underneath specific structural heading blocks.
    """
    pattern = rf"(?:^|\n)##\s*{re.escape(heading_title)}[ \t]*\n(.*?)(?=\n##\s*|\Z)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Fallback to loose structural checks
    fallback_pattern = rf"{re.escape(heading_title)}[^\n]*\n(.*?)(?=\n[A-Z][a-zA-Z\s]{4,}|\Z)"
    fallback_match = re.search(fallback_pattern, text, re.DOTALL | re.IGNORECASE)
    if fallback_match:
        return fallback_match.group(1).strip()

    return ""


def _clean_inline_markdown(text: str) -> str:
    """
    Escapes HTML characters and parses inline bold/italic markdown.
    """
    # Strip pseudo-HTML wrapper tags
    text = re.sub(r"</?(summary|recommendations|roadmap|risks|metadata)>", "", text, flags=re.IGNORECASE)
    
    text = html.escape(text)
    
    # Machine string cleanups
    text = re.sub(r"TERMINATE\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"INVOLVED_AGENTS:\s*.+$", "", text, flags=re.MULTILINE | re.IGNORECASE)
    
    # Bold and Italic formatting conversion
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.*?)\*", r"<i>\1</i>", text)
    
    return text


def add_markdown_to_story(story: list, text: str, styles: Any):
    """
    Parses a markdown string and appends formatted ReportLab flowables to the story.
    Handles headers, bullet lists, bold/italic markup, and removes metadata blocks.
    """
    # Remove metadata blocks
    text = re.sub(r"\[METADATA\].*?\[/METADATA\]", "", text, flags=re.DOTALL | re.IGNORECASE)
    
    # Split into blocks by double newlines (paragraphs/lists)
    blocks = text.split("\n\n")
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        
        # Check if block is a heading
        heading_match = re.match(r"^(#+)\s*(.*?)$", block)
        if heading_match:
            level = len(heading_match.group(1))
            heading_text = _clean_inline_markdown(heading_match.group(2))
            if level == 1:
                story.append(Paragraph(heading_text, styles["ReportH1"]))
            else:
                story.append(Paragraph(heading_text, styles["ReportH2"]))
            continue
        
        # Check if block is a bullet list
        lines = block.split("\n")
        is_bullet_list = all(re.match(r"^\s*([-\*•]|\d+\.)", line) for line in lines if line.strip())
        
        if is_bullet_list:
            for line in lines:
                if not line.strip():
                    continue
                # Clean list prefix
                cleaned_line = re.sub(r"^\s*([-\*•]|\d+\.)\s*", "", line)
                cleaned_line = _clean_inline_markdown(cleaned_line)
                story.append(Paragraph(f"• {cleaned_line}", styles["ReportBullet"]))
            story.append(Spacer(1, 4))
            continue
        
        # Normal paragraph (may have single newlines that should be spaces to allow reflow)
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if re.match(r"^([-\*•]|\d+\.)", line):
                # This line is a list item inside a paragraph block
                cleaned_line = re.sub(r"^([-\*•]|\d+\.)\s*", "", line)
                cleaned_line = _clean_inline_markdown(cleaned_line)
                story.append(Paragraph(f"• {cleaned_line}", styles["ReportBullet"]))
            else:
                cleaned_lines.append(_clean_inline_markdown(line))
        
        if cleaned_lines:
            paragraph_text = " ".join(cleaned_lines)
            story.append(Paragraph(paragraph_text, styles["ReportBody"]))


def generate_pdf_report(problem: str, history: List[AgentResponse], output_path: str) -> str:
    # Initialize basic stylesheet
    styles = getSampleStyleSheet()

    # Custom Brand Palette definitions
    PRIMARY_COLOR = colors.HexColor("#1E3A8A")   # Deep Corporate Indigo
    TEXT_COLOR = colors.HexColor("#1E293B")      # Charcoal Body Text
    MUTED_COLOR = colors.HexColor("#64748B")     # Cool Slate
    BG_LIGHT = colors.HexColor("#F8FAFC")        # Off-white asset card backgrounds

    # Explicit Style Overrides
    styles.add(ParagraphStyle(
        name="CoverTitle",
        fontName="Helvetica-Bold",
        fontSize=32,
        leading=38,
        textColor=PRIMARY_COLOR,
        spaceAfter=15
    ))

    styles.add(ParagraphStyle(
        name="CoverSubtitle",
        fontName="Helvetica",
        fontSize=14,
        leading=18,
        textColor=MUTED_COLOR,
        spaceAfter=40
    ))

    styles.add(ParagraphStyle(
        name="ReportH1",
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=PRIMARY_COLOR,
        spaceBefore=18,
        spaceAfter=10,
        keepWithNext=True
    ))

    styles.add(ParagraphStyle(
        name="ReportH2",
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    ))

    styles.add(ParagraphStyle(
        name="ReportBody",
        fontName="Helvetica",
        fontSize=10,
        leading=15,
        textColor=TEXT_COLOR,
        spaceAfter=8
    ))

    styles.add(ParagraphStyle(
        name="AppendixMeta",
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=12,
        textColor=PRIMARY_COLOR,
        spaceBefore=4,
        spaceAfter=4,
        keepWithNext=True
    ))

    styles.add(ParagraphStyle(
        name="ReportBullet",
        parent=styles["ReportBody"],
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    ))

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=72,
        bottomMargin=72
    )

    story = []

    # ==========================================
    # COVER PAGE
    # ==========================================
    story.append(Spacer(1, 2 * inch))
    story.append(Paragraph("AI Product Strategy Report", styles["CoverTitle"]))
    story.append(HRFlowable(width="100%", thickness=4, color=PRIMARY_COLOR, spaceBefore=5, spaceAfter=15))
    story.append(Paragraph("Cross-Functional Workspace Consensus Output", styles["CoverSubtitle"]))

    story.append(Spacer(1, 2 * inch))
    metadata_text = f"""
    <b>Generated On:</b> {datetime.now().strftime('%B %d, %Y at %H:%M')}<br/>
    <b>Workspace Engine:</b> Multi-Agent Core V2<br/>
    """
    story.append(Paragraph(metadata_text, styles["ReportBody"]))
    story.append(PageBreak())

    # ==========================================
    # MISSION / PROBLEM STATEMENT
    # ==========================================
    story.append(Paragraph("Operational Problem Statement", styles["ReportH1"]))
    add_markdown_to_story(story, problem, styles)
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E2E8F0"), spaceAfter=15))

    # Pull latest final decision text blocks for the summary elements
    final_decision_obj = next((r for r in reversed(history) if r.stage == "final_decision" and r.agent == "manager"), None)
    final_text = final_decision_obj.content if final_decision_obj else ""

    # ==========================================
    # EXECUTIVE SUMMARY
    # ==========================================
    story.append(Paragraph("Executive Summary", styles["ReportH1"]))
    exec_summary = _extract_section(final_text, "Executive Summary")
    if not exec_summary:
        # Fallback if structural slicing didn't isolate block
        exec_summary = final_text.split("##")[0] if final_text else "Consensus runtime finalized successfully."
    add_markdown_to_story(story, exec_summary, styles)
    story.append(Spacer(1, 10))

    # ==========================================
    # PRIORITIZED RECOMMENDATIONS
    # ==========================================
    story.append(Paragraph("Prioritized Recommendations", styles["ReportH1"]))
    recs = _extract_section(final_text, "Why This Decision") or _extract_section(final_text, "Final Recommendation")
    if not recs:
        recs = "Review comprehensive analysis attached below in structural workspace transcripts."
    add_markdown_to_story(story, recs, styles)
    story.append(Spacer(1, 10))

    # ==========================================
    # IMPLEMENTATION ROADMAP
    # ==========================================
    story.append(Paragraph("Implementation Roadmap", styles["ReportH1"]))
    roadmap = _extract_section(final_text, "Next Validation Step")
    if not roadmap:
        roadmap = "Iterative steps described inside baseline discussion indexes."
    add_markdown_to_story(story, roadmap, styles)
    story.append(Spacer(1, 10))

    # ==========================================
    # REMAINING RISKS
    # ==========================================
    story.append(Paragraph("Remaining Risks", styles["ReportH1"]))
    risks = _extract_section(final_text, "Remaining Risks") or _extract_section(final_text, "Alternatives Rejected")
    if not risks:
        risks = "No major immediate engineering constraints tracked."
    add_markdown_to_story(story, risks, styles)

    # ==========================================
    # TEAM DISCUSSION APPENDIX (GROUPED BY STAGE)
    # ==========================================
    story.append(PageBreak())
    story.append(Paragraph("Appendix: Team Deliberation Transcripts", styles["ReportH1"]))
    story.append(Paragraph("Prism log showing the isolated history traces of all distinct alignment rounds.", styles["ReportBody"]))
    story.append(Spacer(1, 10))

    stages_to_print = [
        ("round_1", "Stage 1: Independent Baseline Analysis"),
        ("manager_review", "Stage 2: Cross-Functional Alignment Review"),
        ("targeted_discussion", "Stage 3: Targeted Conflict Resolution")
    ]


    for stage_key, stage_title in stages_to_print:
        stage_responses = [r for r in history if r.stage == stage_key]
        if not stage_responses:
            continue

        story.append(Paragraph(stage_title, styles["ReportH2"]))
        story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY_COLOR, spaceAfter=10))

        for resp in stage_responses:
            # Grouping each single post execution block structurally to protect page layout allocations
            post_block = []
            post_block.append(Paragraph(f"<b>Agent:</b> {resp.label}", styles["AppendixMeta"]))
            post_block.append(Spacer(1, 4))
            add_markdown_to_story(post_block, resp.content, styles)
            post_block.append(Spacer(1, 12))
            story.append(KeepTogether(post_block))

        story.append(Spacer(1, 10))

    doc.build(story, canvasmaker=NumberedCanvas)
    return output_path
