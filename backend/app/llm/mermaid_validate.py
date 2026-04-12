"""
Lightweight Mermaid sanity checks (heuristic; does not parse full grammar).

For stronger validation, PDF export can optionally render via Kroki (see `mermaid_render.fetch_mermaid_png`);
a failed render there results in text-only PDF without implying a formal syntax proof.
"""

from __future__ import annotations

import re

# Known Mermaid diagram type starters (first substantive line after %% comments).
_DIAGRAM_TYPE = re.compile(
    r"^(flowchart|graph|sequenceDiagram|classDiagram|stateDiagram-v2|stateDiagram|erDiagram|"
    r"gitGraph|gantt|pie|mindmap|timeline|journey|block-beta|sankey-beta|kanban|quadrantChart|requirementDiagram|"
    r"xychart-beta|packet-beta|zenuml|C4Context|C4Container|C4Component|C4Dynamic|C4Deployment)\b",
    re.IGNORECASE,
)


def mermaid_lint_warnings(diagram: str) -> list[str]:
    """
    Return user-facing warnings when the diagram text looks structurally invalid.
    Post-ID sanitization does not repair syntax; these flags help reviewers notice issues early.
    """
    warnings: list[str] = []
    if diagram is None:
        return ["[Diagram] Mermaid block is missing."]

    raw = diagram.strip()
    if not raw:
        return ["[Diagram] Mermaid block is empty."]

    # Odd number of triple-backtick fences usually means broken embedding in markdown.
    if raw.count("```") % 2 != 0:
        warnings.append(
            "[Diagram] Unbalanced ``` fences detected inside the diagram text; rendering may fail until fences match."
        )

    lines = [ln.rstrip() for ln in raw.splitlines()]
    substantive: list[str] = []
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if s.startswith("%%"):
            continue
        substantive.append(s)

    if not substantive:
        return warnings + ["[Diagram] No non-comment lines found in the Mermaid block."]

    first = substantive[0].lower()
    # Subgraph-only fragments without outer diagram type are invalid in many renderers.
    if first.startswith("subgraph") and not any(
        _DIAGRAM_TYPE.match(substantive[i]) for i in range(min(5, len(substantive)))
    ):
        warnings.append(
            "[Diagram] Starts with `subgraph` without a preceding `flowchart`/`graph`/… declaration; "
            "many renderers require a diagram type line first."
        )
    elif not _DIAGRAM_TYPE.match(substantive[0]):
        warnings.append(
            "[Diagram] First line does not look like a standard Mermaid diagram declaration "
            "(e.g. `flowchart TD`, `graph LR`, `sequenceDiagram`). Verify syntax for your Mermaid version."
        )

    return warnings
