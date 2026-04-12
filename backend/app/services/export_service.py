import textwrap
from io import BytesIO
from pathlib import Path
from typing import Literal

from PIL import Image

from app.schemas.design import DesignInputPayload, DesignOutputPayload
from app.services.mermaid_render import fetch_mermaid_png


ExportFormat = Literal["markdown", "pdf"]


def _dejavu_sans_path() -> Path:
    # backend layout: /app/app/services/thisfile.py -> parents[2] == /app
    return Path(__file__).resolve().parents[2] / "assets" / "fonts" / "DejaVuSans.ttf"


def _section_list(title: str, items: list[str]) -> list[str]:
    if not items:
        return [f"## {title}", "_None listed._", ""]
    return [f"## {title}", *[f"- {item}" for item in items], ""]


def build_markdown_export(design_title: str, design_input: DesignInputPayload, output: DesignOutputPayload) -> str:
    scorecard = output.architecture_scorecard
    lines: list[str] = [
        f"# {design_title}",
        "",
        "## Input Context",
        f"- Project type: {design_input.project_type}",
        f"- Expected users: {design_input.expected_users}",
        f"- Budget sensitivity: {design_input.budget_sensitivity}",
        f"- Deployment scope: {design_input.deployment_scope}",
        "",
        "## Executive Summary",
        output.executive_summary,
        "",
        "## Architecture Summary",
        output.high_level_architecture,
        "",
        *_section_list("Assumptions", output.assumptions),
        *_section_list("Architecture decisions", output.architecture_decisions),
        *_section_list("Open questions", output.open_questions),
        *_section_list("Consistency & tension warnings", output.consistency_warnings),
        *_section_list("Functional Requirements", output.functional_requirements),
        *_section_list("Non-Functional Requirements", output.non_functional_requirements),
        *_section_list("Core Components", output.core_components),
        *_section_list("Scalability Plan", output.scalability_plan),
        *_section_list("Reliability & Failure Points", output.reliability_and_failure_points),
        *_section_list("Security Considerations", output.security_considerations),
        *_section_list("Cost Considerations", output.cost_considerations),
        *_section_list("Trade-Off Decisions", output.tradeoff_decisions),
        "## Architecture Scorecard",
        f"- Scalability: {scorecard.scalability}/10",
        f"- Reliability: {scorecard.reliability}/10",
        f"- Security: {scorecard.security}/10",
        f"- Maintainability: {scorecard.maintainability}/10",
        f"- Cost Efficiency: {scorecard.cost_efficiency}/10",
        f"- Simplicity: {scorecard.simplicity}/10",
        f"- Biggest Risk: {scorecard.biggest_risk}",
        f"- Biggest Bottleneck: {scorecard.biggest_bottleneck}",
        f"- First Optimization: {scorecard.first_optimization}",
        f"- Avoid Overengineering: {scorecard.avoid_overengineering}",
        "",
        *_section_list("Implementation Roadmap", output.recommended_implementation_phases),
        "## Implementation Checklist",
        *[f"- [ ] {item}" for item in output.engineering_checklist],
        "",
        "## Architecture diagram (Mermaid)",
        "```mermaid",
        output.suggested_mermaid_diagram,
        "```",
        "",
        "## Final Recommendation",
        output.final_recommendation,
    ]
    return "\n".join(lines)


def render_export_content(
    design_title: str,
    design_input: DesignInputPayload,
    output: DesignOutputPayload,
    export_format: ExportFormat = "markdown",
) -> str:
    if export_format == "markdown":
        return build_markdown_export(design_title, design_input, output)
    raise NotImplementedError("Use build_pdf_bytes for PDF")


def _emit_wrapped_line(pdf, raw_line: str, line_height: float, *, ascii_only: bool) -> None:
    """Write one logical line with hard-wrap so fpdf never hits 'single character too wide'."""
    epw = pdf.epw
    s = raw_line if raw_line else " "
    if ascii_only:
        s = s.encode("latin-1", "replace").decode("latin-1")
    chunks = textwrap.wrap(s, width=95, break_long_words=True, break_on_hyphens=False) or [" "]
    for chunk in chunks:
        pdf.multi_cell(w=epw, h=line_height, text=chunk, new_x="LMARGIN", new_y="NEXT")


def build_pdf_bytes(design_title: str, design_input: DesignInputPayload, output: DesignOutputPayload) -> bytes:
    """PDF export with Unicode (Turkish, etc.) when DejaVu Sans is available; optional Kroki PNG for Mermaid."""
    from fpdf import FPDF

    text = build_markdown_export(design_title, design_input, output)
    png = fetch_mermaid_png(output.suggested_mermaid_diagram or "")
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.set_margins(12, 14, 12)
    pdf.add_page()
    font_path = _dejavu_sans_path()
    use_dejavu = font_path.is_file()
    if use_dejavu:
        pdf.add_font("DejaVuSans", "", str(font_path))
        pdf.set_font("DejaVuSans", size=9)
        for raw_line in text.splitlines():
            _emit_wrapped_line(pdf, raw_line, 4.5, ascii_only=False)
    else:
        pdf.set_font("Helvetica", size=9)
        for raw_line in text.splitlines():
            _emit_wrapped_line(pdf, raw_line, 4.5, ascii_only=True)

    if png:
        try:
            pdf.add_page()
            pdf.set_font("DejaVuSans" if use_dejavu else "Helvetica", size=11)
            epw = pdf.epw
            pdf.multi_cell(w=epw, h=6, text="Architecture diagram (rendered)", new_x="LMARGIN", new_y="NEXT")
            im = Image.open(BytesIO(png))
            pdf.image(im, w=epw)
        except Exception:
            pass

    out = pdf.output()
    if isinstance(out, (bytes, bytearray)):
        return bytes(out)
    return str(out).encode("latin-1", "replace")
