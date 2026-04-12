"""
Heuristic consistency checks between structured input and generated output hints.

These rules are intentionally lightweight: they can miss real issues or occasionally
flag tensions that you accept as product trade-offs. Treat `consistency_warnings`
as review prompts, not as formal verification.
"""

import re

from app.schemas.design import DesignInputPayload, DesignOutputPayload


def _digits_in_text(text: str) -> list[int]:
    return [int(m.group(0)) for m in re.finditer(r"\d{3,7}", text.replace(",", ""))]


def analyze_input_consistency(
    inp: DesignInputPayload,
    output: DesignOutputPayload | None = None,
) -> list[str]:
    """
    Returns human-readable warnings when stated constraints appear to conflict
    (e.g. SQLite + very large user targets, single-server + global deployment).
    """
    warnings: list[str] = []
    stack = (inp.preferred_stack or "").lower()
    constraints = inp.constraints.lower()
    problem = inp.problem_statement.lower()
    users_text = f"{inp.expected_users} {problem} {constraints}"

    # --- Datastore vs scale
    if "sqlite" in stack:
        nums = _digits_in_text(users_text)
        if any(n >= 50_000 for n in nums):
            warnings.append(
                "Stated scale (very large user base) together with SQLite in the preferred stack is a strong tension: "
                "SQLite is a great MVP choice but plan an explicit migration path to a client/server database before "
                "multi-instance writes or HA requirements."
            )
        elif any(n >= 5_000 for n in nums):
            warnings.append(
                "SQLite plus mid/high user targets: validate write concurrency and backup/restore early; "
                "consider PostgreSQL if you need multiple app instances writing concurrently."
            )

    if "sqlite" in problem or "sqlite" in constraints:
        if inp.deployment_scope in {"multi-region", "global"}:
            warnings.append(
                "Global or multi-region deployment with SQLite as the primary store is usually impractical for shared "
                "writable state; document regional read replicas or move primary data to a networked RDBMS."
            )

    # --- Single server vs traffic
    if "single server" in constraints or "tek sunucu" in constraints:
        if inp.real_time_required and ("100000" in users_text.replace(" ", "") or "100.000" in users_text):
            warnings.append(
                "Single-server constraint conflicts with very large audience wording: clarify whether this is total "
                "registered users vs concurrent load; realtime fan-out may require horizontal scaling sooner than a single box."
            )

    # --- Budget vs reliability
    if inp.budget_sensitivity == "high" and inp.data_sensitivity in {"high", "critical"}:
        warnings.append(
            "High data sensitivity with tight budget: ensure compliance and security work are explicitly scoped "
            "(logging, access reviews, key management) so cost cuts do not silently remove controls."
        )

    # --- Output cross-check (optional)
    if output is not None:
        out_text = (output.executive_summary + " " + output.high_level_architecture).lower()
        if "sqlite" in stack and "postgres" in out_text and "sqlite" not in out_text:
            warnings.append(
                "Preferred stack includes SQLite but the narrative emphasizes PostgreSQL-like patterns — align on one "
                "primary persistence story or spell out the migration milestone."
            )

    return warnings
