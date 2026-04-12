import pytest

from app.core.config import get_settings
from app.services.mermaid_render import fetch_mermaid_png


@pytest.fixture
def render_enabled(monkeypatch):
    monkeypatch.setenv("MERMAID_PDF_RENDER_ENABLED", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_fetch_mermaid_png_skips_when_disabled(monkeypatch):
    monkeypatch.setenv("MERMAID_PDF_RENDER_ENABLED", "false")
    get_settings.cache_clear()
    assert fetch_mermaid_png("flowchart LR\nA-->B") is None


def test_fetch_mermaid_png_empty_whitespace(render_enabled):
    assert fetch_mermaid_png("   \n") is None


def test_fetch_mermaid_png_kroki_returns_png(render_enabled):
    png = fetch_mermaid_png("flowchart LR\nA-->B")
    if png is None:
        pytest.skip("Kroki unreachable in this environment")
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
