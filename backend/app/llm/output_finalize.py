"""Post-process model output: Mermaid IDs, consistency warnings, default structured sections."""

from __future__ import annotations

from app.llm.consistency import analyze_input_consistency
from app.llm.mermaid_sanitize import sanitize_mermaid
from app.llm.mermaid_validate import mermaid_lint_warnings
from app.schemas.design import DesignInputPayload, DesignOutputPayload, ScaleStance


def _default_assumptions(inp: DesignInputPayload) -> list[str]:
    return [
        f"Problem scope is understood as: {inp.project_type} with constraints: {inp.constraints[:280]}{'…' if len(inp.constraints) > 280 else ''}",
        f"Traffic and scale inputs (expected users / traffic) are directional, not guarantees: {inp.expected_users}; {inp.traffic_assumptions}",
        f"Deployment intent: {inp.deployment_scope}; data sensitivity: {inp.data_sensitivity}",
    ]


def _default_decisions(inp: DesignInputPayload, stance: ScaleStance) -> list[str]:
    base = [
        f"Primary persistence and stack direction follows preferred stack when stated: {inp.preferred_stack or 'not locked — choose boring defaults'}",
        f"Service decomposition stance: {'minimal surface area first' if stance == 'conservative' else 'bounded contexts when metrics justify' if stance == 'balanced' else 'earlier extraction of hot paths when SLO pressure is clear'}",
    ]
    if inp.real_time_required:
        base.append("Realtime transport is in-scope; durable state remains source of truth for recovery and audits.")
    return base


def _default_questions(inp: DesignInputPayload) -> list[str]:
    qs = [
        "What are the top 3 user journeys that must never break during an incident?",
        "What is the maximum acceptable recovery time for the primary datastore?",
    ]
    if inp.deployment_scope != "single-region":
        qs.append("Which data must remain region-local vs globally replicated?")
    return qs


def finalize_design_output(
    payload: DesignOutputPayload,
    inp: DesignInputPayload,
    *,
    scale_stance: ScaleStance = "balanced",
) -> DesignOutputPayload:
    data = payload.model_dump()
    data["suggested_mermaid_diagram"] = sanitize_mermaid(data.get("suggested_mermaid_diagram") or "")

    merged = DesignOutputPayload.model_validate(data)
    auto_warnings = analyze_input_consistency(inp, merged)
    diagram_warnings = mermaid_lint_warnings(data.get("suggested_mermaid_diagram") or "")
    combined = list(
        dict.fromkeys([*(data.get("consistency_warnings") or []), *auto_warnings, *diagram_warnings])
    )
    data["consistency_warnings"] = combined

    if not data.get("assumptions"):
        data["assumptions"] = _default_assumptions(inp)
    if not data.get("architecture_decisions"):
        data["architecture_decisions"] = _default_decisions(inp, scale_stance)
    if not data.get("open_questions"):
        data["open_questions"] = _default_questions(inp)

    return DesignOutputPayload.model_validate(data)
