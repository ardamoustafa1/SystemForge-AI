"""Render Mermaid source to PNG via Kroki (optional; for PDF embedding)."""

from __future__ import annotations

import httpx

from app.core.config import get_settings


def fetch_mermaid_png(diagram: str) -> bytes | None:
    """
    Returns PNG bytes if Kroki succeeds; None if disabled, empty input, network error, or non-200.
    """
    settings = get_settings()
    if not settings.mermaid_pdf_render_enabled:
        return None
    if not diagram or not diagram.strip():
        return None
    url = settings.kroki_url.rstrip("/")
    payload = {
        "diagram_source": diagram.strip(),
        "diagram_type": "mermaid",
        "output_format": "png",
    }
    try:
        with httpx.Client(timeout=settings.kroki_timeout_seconds) as client:
            r = client.post(url, json=payload, headers={"Content-Type": "application/json"})
        if r.status_code != 200:
            return None
        if not r.content[:8].startswith(b"\x89PNG\r\n\x1a\n"):
            return None
        return r.content
    except (httpx.HTTPError, OSError, ValueError):
        return None
