import hashlib

from app.schemas.design import (
    AIArchitectureSection,
    DatabaseArchitectureSection,
    DataFlowSection,
    DesignInputPayload,
    DesignOutputPayload,
    ObservabilityArchitectureSection,
    RuntimeTopologySection,
    ScaleStance,
    SecurityArchitectureSection,
    VideoStreamingArchitectureSection,
    WebsocketArchitectureSection,
)


def _truncate(text: str, max_len: int) -> str:
    t = text.strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 1].rstrip() + "…"


def _score_seed(inp: DesignInputPayload) -> int:
    raw = f"{inp.project_title}|{inp.problem_statement}|{inp.traffic_assumptions}|{inp.constraints}"
    return int(hashlib.sha256(raw.encode("utf-8")).hexdigest(), 16)


def _score_dimension(seed: int, index: int) -> int:
    # Stable per project, spread across 5–10
    return 5 + (seed >> (index * 4)) % 6


def _estimate_monthly_cost_baseline(inp: DesignInputPayload) -> tuple[int, int, list[str]]:
    expected_text = (inp.expected_users or "").lower()
    traffic_text = (inp.traffic_assumptions or "").lower()

    base = 120
    if "k" in expected_text:
        base += 250
    if "m" in expected_text:
        base += 900
    if any(token in expected_text for token in ["100", "200", "500"]):
        base += 180

    if any(token in traffic_text for token in ["burst", "spike", "high", "peak"]):
        base += 180
    if any(token in traffic_text for token in ["realtime", "stream", "websocket"]):
        base += 220

    if inp.deployment_scope == "multi-region":
        base = int(base * 1.4)
    elif inp.deployment_scope == "global":
        base = int(base * 1.9)

    if inp.data_sensitivity in {"high", "critical"}:
        base = int(base * 1.25)

    if inp.real_time_required:
        base += 180

    monthly_min = max(80, int(base * 0.75))
    monthly_max = max(monthly_min + 80, int(base * 1.45))
    breakdown = [
        "Core compute and API runtime capacity",
        "Primary datastore, backups, and storage growth",
        "Network egress and observability tooling",
    ]
    return monthly_min, monthly_max, breakdown


def build_fallback_output(input_payload: DesignInputPayload, scale_stance: ScaleStance = "balanced") -> DesignOutputPayload:
    """
    Deterministic, schema-safe output when no LLM is configured or the provider fails.
    Content is parameterized from DesignInputPayload so different projects read differently.
    """
    inp = input_payload
    title = inp.project_title.strip()
    problem = _truncate(inp.problem_statement, 520)
    stack = (inp.preferred_stack or "").strip()
    stack_bits = [s.strip() for s in stack.replace(";", ",").split(",") if s.strip()][:4]
    seed = _score_seed(inp)

    # --- Functional requirements: reflect domain + realtime + sensitivity
    functional_requirements = [
        f"Deliver core workflows for {inp.project_type} aligned with: {_truncate(problem, 180)}",
        "Authentication, authorization, and tenant-safe data access",
    ]
    if inp.real_time_required:
        functional_requirements.append(
            "Realtime delivery: low-latency fan-out, presence/session routing, and idempotent client updates"
        )
    else:
        functional_requirements.append("Stable request/response APIs with clear versioning and backward compatibility")
    if inp.data_sensitivity in {"high", "critical"}:
        functional_requirements.append("Data protection: encryption in transit and at rest, access logging, and least-privilege operations")
    else:
        functional_requirements.append("Operational visibility: structured logs, metrics, and traceability for primary flows")

    # --- Non-functional: tie to traffic, deployment, budget
    nfr = [
        f"Capacity planning anchored to stated scale: {inp.expected_users} expected users; traffic: {inp.traffic_assumptions}",
        f"Deployment footprint: {inp.deployment_scope.replace('-', ' ')} — document failover, backup, and blast-radius targets",
    ]
    if inp.deployment_scope == "single-region":
        nfr.append("Optimize for regional redundancy within one region before expanding topology")
    elif inp.deployment_scope == "multi-region":
        nfr.append("Define replication strategy (leader/follower or multi-primary), target RPO/RTO, and explicit failover runbook across regions")
        nfr.append("Use latency and health-aware geo routing to steer clients to nearest healthy region with deterministic failback")
    else:
        nfr.append("Global UX: latency budgets, edge caching where applicable, and data residency constraints")
        nfr.append("Use geo routing with residency constraints, cross-region replication policy, and automated failover choreography")

    if inp.budget_sensitivity == "high":
        nfr.append("Cost discipline: right-size managed services, autoscaling guardrails, and chargeback visibility")
    else:
        nfr.append("Reliability SLOs with error budgets; alert on burn rate before user-visible degradation")

    # --- Architecture narrative
    if stack_bits:
        stack_sentence = (
            f"Prefer the stated stack ({', '.join(stack_bits)}) as the default integration spine, "
            "keeping boundaries explicit between API, domain logic, and persistence."
        )
    else:
        stack_sentence = (
            "Choose a small, boring stack the team can operate: modular deployment, one primary transactional store, "
            "and optional cache/queue only where measured need appears."
        )

    high_level_architecture = (
        f"Clients and integrations call an API layer that encapsulates {inp.project_type} rules. "
        f"{stack_sentence} "
        f"Background work is isolated so spikes in {inp.traffic_assumptions} do not starve interactive paths."
    )

    core_labels = ["API / application boundary", "Domain modules", "Primary datastore", "Async processing"]
    if inp.real_time_required:
        core_labels.insert(2, "Realtime channel / event routing")
    if stack_bits:
        core = stack_bits + [c for c in core_labels if c not in stack_bits][: max(0, 6 - len(stack_bits))]
    else:
        core = core_labels + ["Cache (optional)", "Message or task queue (optional)"]
    core_components = core[:8]

    data_layer_recommendations = [
        f"Model data around {_truncate(problem, 120)} — avoid premature generic 'entity bags' that hide invariants.",
        "Use migrations, constraints, and idempotent writes on hot paths.",
    ]
    if inp.data_sensitivity == "critical":
        data_layer_recommendations.append("Critical data: HSM/KMS patterns, strict RBAC, and break-glass auditing")
    else:
        data_layer_recommendations.append("Index and partition plans driven by real query shapes, not guesses")

    cache_strategy = (
        "Cache only measured hot reads; use explicit TTLs and invalidation tied to write paths. "
        f"Given {inp.budget_sensitivity} budget sensitivity, avoid multi-layer caches before profiling."
    )
    queue_event_strategy = (
        "Use queues or outbox patterns for retries, notifications, and heavy work — never as a silent correctness layer. "
        + (
            "Realtime side effects should still reconcile to durable state. Apply load shedding for non-critical workloads and priority queues for interactive traffic."
            if inp.real_time_required
            else "Keep worker concurrency bounded to protect the database, with priority queues and controlled load shedding under surge."
        )
    )

    api_notes = [
        f"Constraints to reflect in API design: {_truncate(inp.constraints, 200)}",
        "Idempotency for writes; pagination and rate limits on list endpoints",
    ]

    scalability_plan = [
        f"Scale hypothesis tied to: {inp.expected_users} users and {inp.traffic_assumptions}",
        "Horizontal scale for stateless tiers first; database scale only with evidence (read replicas, partitioning, or selective extraction)",
    ]
    if inp.real_time_required:
        scalability_plan.append("Realtime tier: connection limits, backpressure, and per-tenant fairness")

    reliability_and_failure_points = [
        f"Failure modes implied by scope ({inp.deployment_scope}): network partitions, partial deploys, and dependency timeouts",
        "Protect the database: connection pools, timeouts, and bulkhead patterns for background consumers",
    ]
    if inp.deployment_scope in {"multi-region", "global"}:
        reliability_and_failure_points.append("Document cross-region failover flow: detection -> traffic shift -> replica promotion -> consistency verification -> controlled failback")

    security_considerations = [
        f"Data sensitivity is {inp.data_sensitivity}: align retention, encryption, and access reviews accordingly",
        "AuthN/AuthZ centralized; secrets rotated; dependency scanning in CI",
        "Apply zero-trust between services, enforce fine-grained RBAC/ABAC on resource actions, and define encryption in transit/at rest explicitly",
    ]
    if inp.mode == "interview":
        security_considerations.append("Interview mode: document threat assumptions explicitly for reviewers")

    cost_considerations = [
        f"Budget sensitivity {inp.budget_sensitivity}: prefer managed building blocks and defer expensive mesh/event infra until volume justifies it",
        "Watch egress, storage growth, and LLM/vector spend if added later",
    ]

    tradeoff_decisions = [
        f"Deployment: {inp.deployment_scope} — trade operational simplicity vs latency and availability goals",
        "Modular monolith or well-bounded services: split only on team or load seams supported by metrics",
    ]
    if stack_bits:
        tradeoff_decisions.append(f"Stack fidelity: honor preferred components ({', '.join(stack_bits)}) vs hiring/operational reality")
    else:
        tradeoff_decisions.append("Document vs flexible schema: prefer constraints and migrations until access patterns stabilize")

    phases = [
        f"MVP for {inp.project_type}: core flows covering {_truncate(problem, 100)}",
        "Hardening: observability, backups, runbooks, load tests on critical paths",
        "Scale phase: act on measured bottlenecks (DB, realtime fan-out, or cross-region behavior)",
    ]

    checklist = [
        f"Validate requirements against constraints: {_truncate(inp.constraints, 120)}",
        "Define SLOs and error budgets for top user journeys",
        "Load test the top 3 endpoints under traffic assumptions",
        "Incident response: on-call, escalation, and rollback playbook",
    ]
    if inp.real_time_required:
        checklist.insert(2, "Realtime soak test: reconnect storms, slow consumers, and ordering guarantees")

    # --- Scorecard: deterministic variation + domain bias
    sc = {name: _score_dimension(seed, i) for i, name in enumerate(["scalability", "reliability", "security", "maintainability", "cost_efficiency", "simplicity"])}
    if inp.data_sensitivity in {"high", "critical"}:
        sc["security"] = min(10, sc["security"] + 1)
    if inp.budget_sensitivity == "high":
        sc["cost_efficiency"] = max(1, sc["cost_efficiency"] - 1)
        sc["simplicity"] = min(10, sc["simplicity"] + 1)
    if inp.deployment_scope == "global":
        sc["scalability"] = min(10, sc["scalability"] + 1)
        sc["simplicity"] = max(1, sc["simplicity"] - 1)

    if scale_stance == "conservative":
        sc["simplicity"] = min(10, sc["simplicity"] + 1)
        sc["cost_efficiency"] = min(10, sc["cost_efficiency"] + 1)
        sc["scalability"] = max(1, sc["scalability"] - 1)
    elif scale_stance == "aggressive":
        sc["scalability"] = min(10, sc["scalability"] + 1)
        sc["reliability"] = min(10, sc["reliability"] + 1)
        sc["simplicity"] = max(1, sc["simplicity"] - 1)

    if inp.deployment_scope == "global":
        br = "Cross-region latency, data residency, and operational coordination across geographies"
        bb = "Consistency models between regions and shared identity/configuration stores"
        fo = "Start with a clear multi-region traffic and data partitioning strategy before optimizing micro-optimizations"
    elif inp.deployment_scope == "multi-region":
        br = "Drift between regions (schema, feature flags, caches) causing subtle production divergence"
        bb = "Replication lag and failover readiness under real traffic"
        fo = "Automated failover drills and measurable RPO/RTO per critical dataset"
    else:
        br = f"Underestimating evolving requirements for {inp.project_type} while the data model hardens too early"
        bb = f"Sustained write/read pressure under: {inp.traffic_assumptions}"
        fo = "Establish profiling on real queries and API paths before adding caching layers"

    avoid = (
        "Avoid premature microservices, heavy event meshes, or bespoke infra before "
        f"scale signals from {inp.expected_users} users / stated traffic justify the complexity."
    )

    title_label = _truncate(title, 40)
    if inp.real_time_required:
        mermaid = (
            "flowchart LR\n"
            f"U[Users / {title_label}] --> api_gw[API gateway]\n"
            "api_gw --> domain_core[Domain services]\n"
            "api_gw --> rt_layer[Realtime plane]\n"
            "domain_core --> db_primary[(Primary store)]\n"
            "domain_core --> queue_bg[Queue / workers]\n"
            "rt_layer --> db_primary\n"
            "rt_layer --> presence[Presence / cache]\n"
        )
    else:
        mermaid = (
            "flowchart LR\n"
            f"U[Users / {title_label}] --> api_gw[API gateway]\n"
            "api_gw --> domain_core[Domain services]\n"
            "domain_core --> db_primary[(Primary store)]\n"
            "domain_core --> queue_bg[Queue / workers]\n"
            "queue_bg --> db_primary\n"
        )

    executive_summary = (
        f"{title} ({inp.project_type}): {_truncate(problem, 360)} "
        f"Expected scale: {inp.expected_users}; traffic context: {inp.traffic_assumptions}. "
        f"Key constraints: {_truncate(inp.constraints, 220)}. "
        f"Recommended direction: bounded modular architecture with explicit scaling triggers — "
        f"{'realtime-aware paths and durable reconciliation where needed' if inp.real_time_required else 'strong API and data contracts first'}."
    )

    final_recommendation = (
        f"Ship a narrow, testable slice of {inp.project_type} functionality first, instrument it against {inp.traffic_assumptions}, "
        f"then evolve components as metrics — not templates — demand. Respect {inp.deployment_scope} operational reality and {inp.data_sensitivity} data handling."
    )
    monthly_min, monthly_max, cost_breakdown = _estimate_monthly_cost_baseline(inp)
    runtime_topology = RuntimeTopologySection(
        architecture_style="Modular monolith with bounded runtime surfaces" if not inp.real_time_required else "Modular services with dedicated realtime gateway",
        deployable_units=[
            "Edge/API gateway",
            "Core application service",
            "Background worker pool",
            *([] if not inp.real_time_required else ["WebSocket gateway"]),
            "Primary relational datastore",
            "Redis for cache/presence/pubsub",
        ],
        primary_runtime_paths=[
            "Synchronous user request path terminates at API/application boundary",
            "Heavy or retryable work is delegated to background workers via queue/outbox path",
            *([] if not inp.real_time_required else ["Realtime connections terminate on WebSocket gateway and fan out through Redis-backed routing"]),
        ],
        stateful_components=[
            "Primary datastore for durable business state",
            "Redis for ephemeral coordination, cache, presence, and fanout routing",
        ],
    )
    data_flows = DataFlowSection(
        request_response_flow=[
            "Client -> API gateway -> application service -> primary datastore -> response",
            "Authenticated writes use idempotency and explicit validation before persistence",
        ],
        asynchronous_event_flow=[
            "Client/API -> queue or outbox -> worker -> side effect handler -> durable update",
            "Completed side effects publish follow-up events for notifications, export, or fanout",
        ],
        persistence_flow=[
            "Application service is the only layer allowed to mutate durable state",
            "Background workers reconcile retries against durable records rather than trusting in-memory state",
        ],
        failure_recovery_flow=[
            "On dependency failure, requests degrade with retry-safe errors rather than partial silent success",
            "Queued work is replayable from durable state and can be re-fanned out after worker restart",
        ],
    )
    websocket_architecture = WebsocketArchitectureSection(
        connection_lifecycle=[
            "Client connects to dedicated WebSocket gateway and authenticates session on connect",
            "Gateway maps socket -> user/session and refreshes presence heartbeat in Redis",
        ] if inp.real_time_required else [],
        fanout_strategy=[
            "Gateway publishes logical events into Redis-backed per-user or per-channel fanout streams",
            "Consumers push only authorized events to connected sockets",
        ] if inp.real_time_required else [],
        scaling_strategy=[
            "Run multiple WebSocket gateway replicas behind a load balancer",
            "Use Redis pub/sub or streams as cross-instance backplane so any node can fan out to any connection owner",
        ] if inp.real_time_required else [],
        sticky_session_strategy="Prefer no sticky sessions if Redis-backed socket ownership/presence is implemented; otherwise require short-lived stickiness at the load balancer." if inp.real_time_required else "",
        pubsub_backplane="Redis pub/sub or Redis Streams for cross-node socket routing and fanout coordination." if inp.real_time_required else "",
        channel_partitioning=[
            "Partition channels by workspace_id and logical room/channel id to keep fanout authorization local",
            "Separate high-fanout broadcast channels from low-volume presence/control channels",
        ] if inp.real_time_required else [],
        shard_strategy=[
            "Hash socket ownership by user_id or channel_id to spread active connections across gateway replicas",
            "Move hot channels to dedicated shards when fanout lag or CPU saturation appears",
        ] if inp.real_time_required else [],
        topic_design=[
            "Use logical topics such as presence.updated, message.created, notification.dispatch, and export.completed",
            "Keep domain events separate from transport-level socket delivery events",
        ] if inp.real_time_required else [],
        partition_keys=[
            "user_id for per-user fanout streams",
            "workspace_id:channel_id for room-scoped ordering and replay",
        ] if inp.real_time_required else [],
    )
    ai_architecture = AIArchitectureSection(
        request_guardrails=[
            "Validate payload size and schema before inference",
            "Apply prompt abuse detection, rate limits, and idempotency on generation endpoints",
        ],
        inference_orchestration=[
            "API accepts generation request, persists job/design shell, and enqueues async generation event",
            "Worker builds prompt, calls provider, validates JSON, finalizes output, then persists completed artifact",
        ],
        queue_and_backpressure=[
            "Generation requests flow through queue/stream workers instead of blocking request threads",
            "Worker concurrency should be capped to protect provider quotas and primary datastore",
            "Use priority queues (interactive > bulk) and load shedding on non-critical jobs during sustained overload",
        ],
        model_provider_strategy=[
            "Primary LLM provider behind a provider client abstraction",
            "Fallback deterministic output when provider is unavailable or response is invalid",
        ],
        fallback_and_recovery=[
            "Invalid model output falls back to schema-safe artifact instead of breaking UX",
            "Failed jobs can be requeued from durable state with traceable status",
        ],
    )
    security_architecture = SecurityArchitectureSection(
        auth_flow=[
            "Authenticate user, issue short-lived access token, and protect mutating routes with CSRF",
            "Authorize every design/resource action through workspace membership and role checks",
            "Use zero-trust service-to-service identity and enforce RBAC/ABAC at API and domain boundaries",
        ],
        session_and_refresh_flow=[
            "Rotate refresh sessions server-side and revoke compromised sessions explicitly",
            "Access token expiry should trigger refresh flow instead of forcing full re-login",
        ],
        abuse_protection=[
            "Apply per-user and per-IP rate limiting on auth, generation, export, and sensitive routes",
            "Inspect uploaded context for prompt-injection patterns and sanitize or block when risky",
        ],
        secrets_and_key_management=[
            "Store provider keys in environment variables or a secrets manager, never in code",
            "Use separate secrets per environment and rotate on exposure",
            "Encrypt in transit with TLS/mTLS where needed and encrypt at rest with managed KMS-backed keys",
        ],
        audit_and_compliance=[
            "Emit security audit records for workspace membership, session revocation, and privileged operations",
            "Log enough metadata for investigation without storing sensitive payloads unnecessarily",
        ],
    )
    video_streaming_architecture = VideoStreamingArchitectureSection(
        streaming_protocols=[
            "Use HLS for broad playback compatibility and CDN cacheability",
            "Use WebRTC only for low-latency instructor/interactor paths where sub-second latency matters",
        ] if any(token in f'{inp.project_type} {inp.problem_statement}'.lower() for token in ["video", "stream", "live", "education", "lesson", "course"]) else [],
        ingest_and_packaging=[
            "Ingest broadcaster stream through RTMP or WHIP gateway into packaging pipeline",
            "Package output into multi-bitrate HLS renditions with short segment duration for near-live playback",
        ] if any(token in f'{inp.project_type} {inp.problem_statement}'.lower() for token in ["video", "stream", "live", "education", "lesson", "course"]) else [],
        cdn_strategy=[
            "Push HLS manifests and segments through a CDN with regional edge caching",
            "Protect origin with signed URLs or tokenized playback access for private classes",
        ] if any(token in f'{inp.project_type} {inp.problem_statement}'.lower() for token in ["video", "stream", "live", "education", "lesson", "course"]) else [],
        adaptive_bitrate_strategy=[
            "Generate ABR ladder by source resolution and expected network conditions",
            "Tune player startup bitrate conservatively, then ramp based on bandwidth estimation and rebuffer ratio",
        ] if any(token in f'{inp.project_type} {inp.problem_statement}'.lower() for token in ["video", "stream", "live", "education", "lesson", "course"]) else [],
        realtime_interaction_sidecar=[
            "Keep chat, presence, polls, and reactions on a separate realtime sidecar instead of coupling them to media transport",
        ] if any(token in f'{inp.project_type} {inp.problem_statement}'.lower() for token in ["video", "stream", "live", "education", "lesson", "course"]) else [],
    )
    database_architecture = DatabaseArchitectureSection(
        primary_entities=[
            f"{inp.project_type} primary aggregate",
            "user",
            "workspace",
            "event or activity record",
            *([] if not inp.real_time_required else ["realtime session", "message or interaction record"]),
        ],
        schema_design=[
            "Use transactional tables for source-of-truth entities and separate append-only event tables for audit/history",
            "Represent high-cardinality interactions with narrow hot tables and archive-ready historical tables",
        ],
        indexing_strategy=[
            "Composite indexes should follow dominant access paths such as workspace_id + created_at and owner_id + status",
            "Use covering indexes for list screens and operational queues to reduce random heap lookups",
        ],
        partitioning_strategy=[
            "Partition append-heavy activity tables by time window once retention or write throughput justifies it",
            "Consider tenant-aware partitioning only when workspace cardinality and noisy-neighbor risk are measurable",
        ],
        consistency_and_migration_notes=[
            "Enforce invariants with foreign keys, unique constraints, and idempotency keys before adding async repair jobs",
            "Ship backward-compatible migrations first, then deploy code that reads/writes new columns",
        ],
    )
    observability_architecture = ObservabilityArchitectureSection(
        logging_strategy=[
            "Emit structured JSON logs with trace_id, workspace_id, user_id, and design_id where available",
            "Separate audit/security logs from application debug logs to retain signal under load",
        ],
        tracing_strategy=[
            "Instrument API, worker, DB, Redis, and provider calls with OpenTelemetry spans",
            "Propagate trace context from request edge through queue messages into async workers",
        ],
        metrics_strategy=[
            "Track request latency, queue depth, worker throughput, websocket connection count, fanout lag, and DB pool saturation",
            "Expose model latency, fallback rate, token usage, and provider error classes as first-class metrics",
        ],
        alerting_strategy=[
            "Alert on SLO burn rate, queue backlog growth, fanout delay, elevated fallback rate, and media rebuffer spikes",
            "Page only on user-visible degradation; route capacity warnings and cost anomalies to non-paging channels",
        ],
        sli_slo_targets=[
            "Define SLI/SLOs for API latency, generation success, websocket delivery freshness, and playback start time where video is in scope",
        ],
    )

    payload = {
        "executive_summary": executive_summary,
        "functional_requirements": functional_requirements,
        "non_functional_requirements": nfr,
        "high_level_architecture": high_level_architecture,
        "core_components": core_components,
        "data_layer_recommendations": data_layer_recommendations,
        "cache_strategy": cache_strategy,
        "queue_event_strategy": queue_event_strategy,
        "api_service_design_notes": api_notes,
        "scalability_plan": scalability_plan,
        "reliability_and_failure_points": reliability_and_failure_points,
        "security_considerations": security_considerations,
        "cost_considerations": cost_considerations,
        "tradeoff_decisions": tradeoff_decisions,
        "recommended_implementation_phases": phases,
        "engineering_checklist": checklist,
        "architecture_scorecard": {
            "scalability": sc["scalability"],
            "reliability": sc["reliability"],
            "security": sc["security"],
            "maintainability": sc["maintainability"],
            "cost_efficiency": sc["cost_efficiency"],
            "simplicity": sc["simplicity"],
            "biggest_risk": br,
            "biggest_bottleneck": bb,
            "first_optimization": fo,
            "avoid_overengineering": avoid,
        },
        "suggested_mermaid_diagram": mermaid,
        "final_recommendation": final_recommendation,
        "assumptions": [
            f"Offline template; scale stance: {scale_stance}.",
            f"Problem framing: {_truncate(problem, 240)}",
            f"Stated scale signals: {inp.expected_users}; {inp.traffic_assumptions}",
        ],
        "architecture_decisions": [
            f"Prefer modular boundaries before extra deployables (stance: {scale_stance}).",
            f"Align persistence with preferred stack: {stack or 'choose minimal operational surface first'}",
        ],
        "open_questions": [
            "Which user journeys are revenue- or safety-critical and need stricter SLOs?",
            "What is the expected team size operating this system in production?",
        ],
        "consistency_warnings": [],
        "estimated_cloud_cost": {
            "monthly_usd_min": monthly_min,
            "monthly_usd_max": monthly_max,
            "cost_breakdown": cost_breakdown,
        },
        "runtime_topology": runtime_topology.model_dump(),
        "data_flows": data_flows.model_dump(),
        "websocket_architecture": websocket_architecture.model_dump(),
        "ai_architecture": ai_architecture.model_dump(),
        "security_architecture": security_architecture.model_dump(),
        "video_streaming_architecture": video_streaming_architecture.model_dump(),
        "database_architecture": database_architecture.model_dump(),
        "observability_architecture": observability_architecture.model_dump(),
    }
    return DesignOutputPayload.model_validate(payload)
