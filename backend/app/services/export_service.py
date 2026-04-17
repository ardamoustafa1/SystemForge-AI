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
    multi_region_notes: list[str] = []
    if design_input.deployment_scope in {"multi-region", "global"}:
        multi_region_notes = [
            *output.data_flows.failure_recovery_flow,
            *output.scalability_plan,
            *output.reliability_and_failure_points,
        ]
    backpressure_notes = [
        *output.ai_architecture.queue_and_backpressure,
        output.queue_event_strategy,
    ]
    security_depth_notes = [
        *output.security_architecture.auth_flow,
        *output.security_architecture.secrets_and_key_management,
        *output.security_considerations,
    ]
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
        "## Runtime Topology",
        f"- Architecture style: {output.runtime_topology.architecture_style}",
        "",
        *_section_list("Deployable units", output.runtime_topology.deployable_units),
        *_section_list("Primary runtime paths", output.runtime_topology.primary_runtime_paths),
        *_section_list("Stateful components", output.runtime_topology.stateful_components),
        *_section_list("Request / response flow", output.data_flows.request_response_flow),
        *_section_list("Async event flow", output.data_flows.asynchronous_event_flow),
        *_section_list("Persistence flow", output.data_flows.persistence_flow),
        *_section_list("Failure recovery flow", output.data_flows.failure_recovery_flow),
        *_section_list("WebSocket connection lifecycle", output.websocket_architecture.connection_lifecycle),
        *_section_list("WebSocket fanout strategy", output.websocket_architecture.fanout_strategy),
        *_section_list("WebSocket scaling strategy", output.websocket_architecture.scaling_strategy),
        *_section_list("WebSocket channel partitioning", output.websocket_architecture.channel_partitioning),
        *_section_list("WebSocket shard strategy", output.websocket_architecture.shard_strategy),
        *_section_list("WebSocket topic design", output.websocket_architecture.topic_design),
        *_section_list("WebSocket partition keys", output.websocket_architecture.partition_keys),
        "## WebSocket routing notes",
        output.websocket_architecture.pubsub_backplane or "_Not applicable._",
        "",
        "## Sticky session strategy",
        output.websocket_architecture.sticky_session_strategy or "_Not applicable._",
        "",
        *_section_list("Video streaming protocols", output.video_streaming_architecture.streaming_protocols),
        *_section_list("Video ingest and packaging", output.video_streaming_architecture.ingest_and_packaging),
        *_section_list("Video CDN strategy", output.video_streaming_architecture.cdn_strategy),
        *_section_list("Adaptive bitrate strategy", output.video_streaming_architecture.adaptive_bitrate_strategy),
        *_section_list("Realtime interaction sidecar", output.video_streaming_architecture.realtime_interaction_sidecar),
        *_section_list("Database primary entities", output.database_architecture.primary_entities),
        *_section_list("Database schema design", output.database_architecture.schema_design),
        *_section_list("Database indexing strategy", output.database_architecture.indexing_strategy),
        *_section_list("Database partitioning strategy", output.database_architecture.partitioning_strategy),
        *_section_list("Database consistency and migration notes", output.database_architecture.consistency_and_migration_notes),
        *_section_list("Observability logging strategy", output.observability_architecture.logging_strategy),
        *_section_list("Observability tracing strategy", output.observability_architecture.tracing_strategy),
        *_section_list("Observability metrics strategy", output.observability_architecture.metrics_strategy),
        *_section_list("Observability alerting strategy", output.observability_architecture.alerting_strategy),
        *_section_list("Observability SLI / SLO targets", output.observability_architecture.sli_slo_targets),
        *_section_list("Multi-region strategy", multi_region_notes),
        *_section_list("AI request guardrails", output.ai_architecture.request_guardrails),
        *_section_list("AI inference orchestration", output.ai_architecture.inference_orchestration),
        *_section_list("AI queue and backpressure", output.ai_architecture.queue_and_backpressure),
        *_section_list("AI model provider strategy", output.ai_architecture.model_provider_strategy),
        *_section_list("AI fallback and recovery", output.ai_architecture.fallback_and_recovery),
        *_section_list("Backpressure policy", backpressure_notes),
        *_section_list("Security auth flow", output.security_architecture.auth_flow),
        *_section_list("Security session and refresh flow", output.security_architecture.session_and_refresh_flow),
        *_section_list("Security abuse protection", output.security_architecture.abuse_protection),
        *_section_list("Security secrets and key management", output.security_architecture.secrets_and_key_management),
        *_section_list("Security audit and compliance", output.security_architecture.audit_and_compliance),
        *_section_list("Security depth", security_depth_notes),
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
