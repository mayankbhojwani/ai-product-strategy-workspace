# Original User Request

## Initial Request — 2026-07-10T00:49:19Z

Refactor the ReportLab PDF generator in the workspace to produce a well-structured, robust, and visually premium executive PDF report.

Working directory: /Users/anita/ai-product-strategy-workspace
Integrity mode: development

## Requirements

### R1. Premium Layout & Structural Stability
Refactor the PDF generator (`app/reporting/pdf_report.py`) to resolve layout bugs. Specifically, the generator must:
- Prevent orphan headings (H1/H2 must stay with the next paragraph).
- Avoid text/element overlaps.
- Handle pagination cleanly, ensuring running headers and footers are omitted on the Cover Page but drawn on subsequent pages.
- Standardize margins, font scales, and spacings to ensure a premium executive aesthetic.

### R2. Automated Verification Suite
Implement a Python test suite (e.g., in `tests/test_pdf_structure.py`) to programmatically verify PDF structure. The test suite must:
- Generate dummy agent response histories (including Stage 1, Stage 2, Stage 3, and Stage 4 responses).
- Call the PDF generator to produce a test PDF.
- Programmatically verify that the PDF compiles without errors.
- Parse or verify that the PDF is non-empty and contains all expected sections (Executive Summary, Recommendations, Roadmap, Risks, and Appendix).

## Acceptance Criteria

### Execution & Compilation
- [ ] Refactored PDF generator runs successfully when called from Streamlit or test scripts.
- [ ] No ReportLab layout crashes (like FlowableTooLargeError or infinite loops on page breaks).

### Layout & Spacing
- [ ] Section headings (H1, H2) never appear at the bottom of a page as orphans (must use `keepWithNext=True` styles or similar).
- [ ] Cover page is cleanly separated and has no headers/footers.
- [ ] Running header/footer on subsequent pages correctly displays the report name and "Page X of Y" dynamic page count.

### Automated Test Coverage
- [ ] A dedicated python script/test suite is created to verify these layout constraints with mock inputs.
- [ ] Running this test script returns a success code (exit code 0).
