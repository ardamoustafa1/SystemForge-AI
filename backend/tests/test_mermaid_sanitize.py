from app.llm.mermaid_sanitize import sanitize_mermaid


def test_sanitize_preserves_clean_ascii_ids():
    src = "flowchart LR\n  api --> db[(store)]"
    assert sanitize_mermaid(src) == src


def test_sanitize_maps_non_ascii_node_ids():
    src = "flowchart LR\n  türkçe[API] --> db[(store)]"
    out = sanitize_mermaid(src)
    assert "türkçe" not in out
    assert "n1[" in out
    assert "db" in out


def test_sanitize_edge_non_ascii_without_brackets():
    src = "flowchart LR\n  a --> türkçe"
    out = sanitize_mermaid(src)
    assert "türkçe" not in out
