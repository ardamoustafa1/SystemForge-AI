from app.llm.mermaid_validate import mermaid_lint_warnings


def test_lint_empty_diagram():
    assert any("empty" in w.lower() for w in mermaid_lint_warnings(""))


def test_lint_valid_flowchart_clean():
    d = "flowchart LR\n  A --> B"
    assert mermaid_lint_warnings(d) == []


def test_lint_missing_diagram_type():
    d = "A --> B\nC --> D"
    w = mermaid_lint_warnings(d)
    assert len(w) == 1
    assert "[Diagram]" in w[0]


def test_lint_unbalanced_fences():
    d = "```mermaid\nflowchart LR\n  A --> B"
    w = mermaid_lint_warnings(d)
    assert any("fence" in x.lower() for x in w)
