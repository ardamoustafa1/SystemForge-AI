from app.schemas.design import DesignInputPayload, ScaleStance


def build_system_prompt(scale_stance: ScaleStance = "balanced") -> str:
    stance_block = {
        "conservative": (
            "Scale stance: CONSERVATIVE — prefer the smallest viable architecture, fewer moving parts, "
            "strong modularity inside one deployable, and postpone distributed systems until metrics justify."
        ),
        "balanced": (
            "Scale stance: BALANCED — practical defaults, clear boundaries, scale triggers documented."
        ),
        "aggressive": (
            "Scale stance: AGGRESSIVE — assume faster growth and earlier investment in scalability paths, "
            "but still avoid unmotivated microservices or unnecessary infrastructure."
        ),
    }[scale_stance]

    return (
        "You are a principal staff engineer producing production-grade system design artifacts.\n"
        "Return JSON only. Do not include markdown fences.\n"
        f"{stance_block}\n"
        "Be practical, constraint-aware, and implementation-oriented.\n"
        "Avoid generic language and avoid overengineering.\n"
        "Every major recommendation must include rationale and trade-offs.\n"
        "If constraints appear to conflict (e.g. tiny team + global deployment + strict latency), call that tension out explicitly.\n"
        "Include concrete guidance for code organization, testability, and module boundaries where relevant.\n"
        "Mermaid rules for suggested_mermaid_diagram:\n"
        "- Use flowchart LR or TB.\n"
        "- Node identifiers MUST be ASCII-only: letters, digits, underscore (e.g. api_gw, domain_core, db_primary).\n"
        "- Human-readable titles may appear inside brackets after the id, including non-English text in labels.\n"
        "- Example: api_gw[API Gateway] --> svc_auth[Auth Service]\n"
        "Populate assumptions, architecture_decisions, and open_questions arrays with project-specific content.\n"
        "Populate consistency_warnings only if you infer tensions from the input; otherwise use an empty array.\n"
    )


def build_user_prompt(input_payload: DesignInputPayload, scale_stance: ScaleStance = "balanced") -> str:
    hints: list[str] = []
    stack = (input_payload.preferred_stack or "").lower()
    if "sqlite" in stack:
        hints.append(
            "Input mentions SQLite: explain concurrency limits and when to migrate to a client/server RDBMS."
        )
    if input_payload.deployment_scope == "global":
        hints.append("Input is global scope: address latency, residency, and cross-region data ownership.")

    hints_block = "\n".join(f"- {h}" for h in hints) if hints else "(none)"

    return (
        f"Generate a structured engineering architecture package. Scale stance: {scale_stance}.\n"
        "Honor constraints exactly and produce concrete guidance.\n\n"
        "Additional analytic hints:\n"
        f"{hints_block}\n\n"
        "Project input JSON:\n"
        f"{input_payload.model_dump_json(indent=2)}"
    )
