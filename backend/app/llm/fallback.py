import hashlib

from app.schemas.design import DesignInputPayload, DesignOutputPayload, ScaleStance


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
        nfr.append("Define RPO/RTO across regions; prefer explicit replication and conflict strategy for shared state")
    else:
        nfr.append("Global UX: latency budgets, edge caching where applicable, and data residency constraints")

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
        + ("Realtime side effects should still reconcile to durable state." if inp.real_time_required else "Keep worker concurrency bounded to protect the database.")
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

    security_considerations = [
        f"Data sensitivity is {inp.data_sensitivity}: align retention, encryption, and access reviews accordingly",
        "AuthN/AuthZ centralized; secrets rotated; dependency scanning in CI",
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
    }
    return DesignOutputPayload.model_validate(payload)
