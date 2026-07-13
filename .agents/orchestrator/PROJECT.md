# Project: PDF Report Refactoring and Verification

## Architecture
- `app/reporting/pdf_report.py`: The PDF generator module containing `generate_pdf_report(problem: str, history: List[AgentResponse], output_path: str)` which formats and compiles agent discussions into an executive PDF report.
- `app/orchestration/types.py`: Defines the `AgentResponse` dataclass.
- `tests/test_pdf_structure.py`: The automated test suite that generates dummy response histories, runs the PDF generator, and verifies PDF structure/content.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Exploration & Analysis | Investigate layout issues, overlapping text, margins, and plan refactoring. | None | IN_PROGRESS |
| 2 | Verification Suite | Implement `tests/test_pdf_structure.py` to programmatically verify PDF structure and compilation. | M1 | PLANNED |
| 3 | PDF Layout Refactoring | Refactor `app/reporting/pdf_report.py` to resolve orphan headings, overlap issues, margins, headers/footers. | M2 | PLANNED |
| 4 | Final Verification & Audit | Perform comprehensive verification, reviews, and a Forensic Audit pass. | M3 | PLANNED |

## Interface Contracts
### `app/reporting/pdf_report.py` ↔ `tests/test_pdf_structure.py`
- `generate_pdf_report(problem: str, history: List[AgentResponse], output_path: str) -> str`:
  - Input: `problem` (str), `history` (List[AgentResponse]), `output_path` (str)
  - Output: Returns absolute path to the generated PDF.
  - Exceptions: Should compile cleanly without ReportLab exceptions (like FlowableTooLargeError).

## Code Layout
- `app/reporting/pdf_report.py` - Core PDF report generation logic.
- `tests/test_pdf_structure.py` - Unit and integration tests for report structure, metadata, and pagination.
