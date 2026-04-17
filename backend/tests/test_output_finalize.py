from app.schemas.design import DesignInputPayload, DesignOutputPayload
from app.llm.fallback import build_fallback_output
from app.llm.output_finalize import finalize_design_output
from app.services.export_service import build_markdown_export


def _sample_input() -> DesignInputPayload:
    return DesignInputPayload.model_validate(
        {
            "project_title": "Demo Project Title",
            "project_type": "api",
            "problem_statement": "We need a reliable backend for our product with clear scaling path.",
            "expected_users": "75000",
            "traffic_assumptions": "steady load under 100 rps peak",
            "budget_sensitivity": "medium",
            "preferred_stack": "sqlite,python",
            "constraints": "small team",
            "deployment_scope": "single-region",
            "data_sensitivity": "medium",
            "real_time_required": False,
            "mode": "product",
        }
    )


def test_finalize_merges_diagram_and_consistency_warnings():
    inp = _sample_input()
    base = build_fallback_output(inp)
    data = base.model_dump()
    data["suggested_mermaid_diagram"] = "not_a_diagram_type\n  x --> y"
    data["consistency_warnings"] = ["Custom prior warning"]

    out = finalize_design_output(DesignOutputPayload.model_validate(data), inp)

    assert any("Custom prior warning" in w for w in out.consistency_warnings)
    assert any("[Diagram]" in w for w in out.consistency_warnings)
    assert any("SQLite" in w for w in out.consistency_warnings)


def test_finalize_backfills_blueprint_sections():
    inp = _sample_input()
    base = build_fallback_output(inp)
    data = base.model_dump()
    data["runtime_topology"] = {}
    data["data_flows"] = {}
    data["ai_architecture"] = {}
    data["security_architecture"] = {}
    data["database_architecture"] = {}
    data["observability_architecture"] = {}

    out = finalize_design_output(DesignOutputPayload.model_validate(data), inp)

    assert out.runtime_topology.architecture_style
    assert out.runtime_topology.deployable_units
    assert out.data_flows.request_response_flow
    assert out.ai_architecture.request_guardrails
    assert out.security_architecture.auth_flow
    assert out.database_architecture.primary_entities
    assert out.observability_architecture.logging_strategy


def test_markdown_export_includes_blueprint_sections():
    inp = _sample_input()
    out = finalize_design_output(build_fallback_output(inp), inp)

    markdown = build_markdown_export(inp.project_title, inp, out)

    assert "## Runtime Topology" in markdown
    assert "## WebSocket routing notes" in markdown
    assert "## Sticky session strategy" in markdown
    assert "## AI request guardrails" in markdown
    assert "## Security auth flow" in markdown
    assert "## Database primary entities" in markdown
    assert "## Observability tracing strategy" in markdown
    assert "## Multi-region strategy" in markdown
    assert "## Backpressure policy" in markdown
    assert "## Security depth" in markdown


def test_video_workloads_include_streaming_sections():
    inp = DesignInputPayload.model_validate(
        {
            "project_title": "Live Academy",
            "project_type": "live education streaming",
            "problem_statement": "Build a live education platform with interactive video lessons, chat, and playback support.",
            "expected_users": "150000",
            "traffic_assumptions": "live burst traffic with video streaming and websocket chat",
            "budget_sensitivity": "medium",
            "preferred_stack": "python,postgres,redis",
            "constraints": "small platform team and global learners",
            "deployment_scope": "multi-region",
            "data_sensitivity": "high",
            "real_time_required": True,
            "mode": "product",
        }
    )

    out = finalize_design_output(build_fallback_output(inp), inp)

    assert out.video_streaming_architecture.streaming_protocols
    assert out.video_streaming_architecture.cdn_strategy
    assert out.video_streaming_architecture.adaptive_bitrate_strategy
    assert out.websocket_architecture.channel_partitioning
    assert out.websocket_architecture.partition_keys


def test_finalize_backfills_senior_depth_for_multi_region_and_security():
    inp = DesignInputPayload.model_validate(
        {
            "project_title": "Global Collaboration Suite",
            "project_type": "enterprise collaboration",
            "problem_statement": "Need low-latency global collaboration with strict security and high availability.",
            "expected_users": "500000",
            "traffic_assumptions": "spiky realtime and async workloads",
            "budget_sensitivity": "medium",
            "preferred_stack": "python,postgres,redis",
            "constraints": "small platform team but strict uptime",
            "deployment_scope": "multi-region",
            "data_sensitivity": "critical",
            "real_time_required": True,
            "mode": "product",
        }
    )
    base = build_fallback_output(inp)
    data = base.model_dump()
    data["data_flows"] = {}
    data["ai_architecture"] = {}
    data["security_architecture"] = {}

    out = finalize_design_output(DesignOutputPayload.model_validate(data), inp)

    assert any("Region incident flow" in item for item in out.data_flows.failure_recovery_flow)
    assert any("priority queues" in item.lower() for item in out.ai_architecture.queue_and_backpressure)
    assert any("load shedding" in item.lower() for item in out.ai_architecture.queue_and_backpressure)
    assert any("zero-trust" in item.lower() for item in out.security_architecture.auth_flow)
    assert any("rbac/abac" in item.lower() for item in out.security_architecture.auth_flow)
    assert any("encrypt data in transit" in item.lower() for item in out.security_architecture.secrets_and_key_management)
