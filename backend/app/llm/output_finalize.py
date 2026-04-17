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


def _default_runtime_topology(inp: DesignInputPayload) -> dict:
    return {
        "architecture_style": "Modular service boundary with async workers" if inp.real_time_required else "Modular application with async workers",
        "deployable_units": [
            "API gateway / edge",
            "Application service",
            "Background worker",
            *([] if not inp.real_time_required else ["WebSocket gateway"]),
            "Primary datastore",
            "Redis coordination layer",
        ],
        "primary_runtime_paths": [
            "Synchronous requests terminate in the API/application path",
            "Heavy work is delegated to async workers via queue or outbox",
        ],
        "stateful_components": ["Primary datastore", "Redis for ephemeral coordination"],
    }


def _default_data_flows(inp: DesignInputPayload) -> dict:
    failover_flow = "Retries and replays are driven from durable state, not in-memory assumptions"
    if inp.deployment_scope in {"multi-region", "global"}:
        failover_flow = (
            "Region incident flow: health checks trigger traffic drain, promote replica, and recover within stated RPO/RTO targets"
        )
    return {
        "request_response_flow": ["Client -> API gateway -> application service -> datastore -> response"],
        "asynchronous_event_flow": ["Application -> queue/outbox -> worker -> side effects -> publish/update"],
        "persistence_flow": ["Application and workers reconcile through durable database state"],
        "failure_recovery_flow": [failover_flow],
    }


def _default_websocket_architecture(inp: DesignInputPayload) -> dict:
    if not inp.real_time_required:
        return {}
    return {
        "connection_lifecycle": [
            "Clients connect to a dedicated gateway and authenticate on connect",
            "Gateway stores ephemeral socket ownership and heartbeat state in Redis",
        ],
        "fanout_strategy": [
            "Application publishes logical events to a Redis backplane",
            "Owning gateway instances fan out only to authorized connections",
        ],
        "scaling_strategy": [
            "Scale gateway replicas horizontally behind a load balancer",
            "Use Redis-backed routing so fanout is not node-local",
        ],
        "sticky_session_strategy": "Prefer avoiding sticky sessions when gateway ownership is externalized to Redis.",
        "pubsub_backplane": "Redis pub/sub or streams for cross-node routing.",
        "channel_partitioning": [
            "Partition realtime channels by workspace and room to preserve authorization boundaries",
        ],
        "shard_strategy": [
            "Hash active sockets by user_id or channel_id across gateway shards",
        ],
        "topic_design": [
            "Use domain topics for presence, message, notification, and export lifecycles",
        ],
        "partition_keys": [
            "workspace_id:channel_id for room ordering",
            "user_id for direct fanout",
        ],
    }


def _default_ai_architecture() -> dict:
    return {
        "request_guardrails": [
            "Schema validation and rate limiting before inference",
            "Prompt abuse detection on uploaded context",
        ],
        "inference_orchestration": [
            "Persist job request, enqueue generation, and finalize only after schema validation",
        ],
        "queue_and_backpressure": [
            "Bound worker concurrency and protect provider quotas with queued processing",
            "Use priority queues so user-facing requests are served before batch/backfill workloads",
            "Enable load shedding when queue depth/latency exceeds threshold to protect core interactive paths",
        ],
        "model_provider_strategy": [
            "Provider abstraction around primary LLM plus fallback path",
        ],
        "fallback_and_recovery": [
            "Use deterministic fallback output when provider fails or returns invalid JSON",
        ],
    }


def _default_security_architecture() -> dict:
    return {
        "auth_flow": [
            "Authenticate user and authorize every resource through workspace membership",
            "Adopt zero-trust service boundaries: every internal call is authenticated and authorized",
            "Enforce fine-grained RBAC/ABAC checks per action, tenant, and resource scope",
        ],
        "session_and_refresh_flow": [
            "Use short-lived access tokens and refresh-session rotation",
        ],
        "abuse_protection": [
            "Apply per-route rate limits and abuse scoring on risky inputs",
        ],
        "secrets_and_key_management": [
            "Store secrets outside code and rotate them per environment",
            "Encrypt data in transit with TLS and encrypt data at rest using managed KMS keys with rotation",
        ],
        "audit_and_compliance": [
            "Audit privileged actions and security-sensitive state changes",
        ],
    }


def _default_video_streaming_architecture(inp: DesignInputPayload) -> dict:
    text = f"{inp.project_type} {inp.problem_statement}".lower()
    if not any(token in text for token in ["video", "stream", "live", "education", "lesson", "course"]):
        return {}
    return {
        "streaming_protocols": [
            "HLS for playback reach and CDN compatibility",
            "WebRTC for low-latency interactive instructor paths only",
        ],
        "ingest_and_packaging": [
            "RTMP or WHIP ingest into packaging/transcoding pipeline",
            "Generate short-segment multi-bitrate HLS outputs",
        ],
        "cdn_strategy": [
            "Serve segments and manifests through a CDN with edge caching",
        ],
        "adaptive_bitrate_strategy": [
            "Use ABR ladder selection based on bandwidth estimation and rebuffer tolerance",
        ],
        "realtime_interaction_sidecar": [
            "Handle chat, polls, and reactions via separate realtime services rather than media transport",
        ],
    }


def _default_database_architecture() -> dict:
    return {
        "primary_entities": ["primary domain aggregate", "user", "workspace", "activity/event"],
        "schema_design": [
            "Use transactional normalized tables for source-of-truth entities and append-only history where needed",
        ],
        "indexing_strategy": [
            "Create composite indexes matching primary list/filter paths and queue access patterns",
        ],
        "partitioning_strategy": [
            "Time-partition append-heavy history tables when write volume or retention justifies it",
        ],
        "consistency_and_migration_notes": [
            "Prefer FK/unique constraints and expand-migrate-contract rollout for schema changes",
        ],
    }


def _default_observability_architecture() -> dict:
    return {
        "logging_strategy": [
            "Use structured logs with request and trace correlation fields",
        ],
        "tracing_strategy": [
            "Use OpenTelemetry spans across API, workers, Redis, DB, and provider calls",
        ],
        "metrics_strategy": [
            "Track latency, queue depth, connection count, fanout lag, and provider fallback/error rates",
        ],
        "alerting_strategy": [
            "Alert on SLO burn, backlog growth, dependency error spikes, and user-visible degradation",
        ],
        "sli_slo_targets": [
            "Define SLIs for request latency, async success, and realtime freshness",
        ],
    }


def _merge_missing_fields(current: dict | None, defaults: dict) -> dict:
    merged = dict(current or {})
    for key, value in defaults.items():
        existing = merged.get(key)
        if existing in (None, "", []):
            merged[key] = value
    return merged


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
    data["runtime_topology"] = _merge_missing_fields(data.get("runtime_topology"), _default_runtime_topology(inp))
    data["data_flows"] = _merge_missing_fields(data.get("data_flows"), _default_data_flows(inp))
    data["websocket_architecture"] = _merge_missing_fields(
        data.get("websocket_architecture"),
        _default_websocket_architecture(inp),
    )
    data["ai_architecture"] = _merge_missing_fields(data.get("ai_architecture"), _default_ai_architecture())
    data["security_architecture"] = _merge_missing_fields(
        data.get("security_architecture"),
        _default_security_architecture(),
    )
    data["video_streaming_architecture"] = _merge_missing_fields(
        data.get("video_streaming_architecture"),
        _default_video_streaming_architecture(inp),
    )
    data["database_architecture"] = _merge_missing_fields(
        data.get("database_architecture"),
        _default_database_architecture(),
    )
    data["observability_architecture"] = _merge_missing_fields(
        data.get("observability_architecture"),
        _default_observability_architecture(),
    )

    return DesignOutputPayload.model_validate(data)
