from __future__ import annotations

import base64
import json
from typing import Literal
from uuid import uuid4

from app.core.config import get_settings
from app.core.redis import get_redis_client
from app.schemas.design import DesignInputPayload, DesignOutputPayload
from app.services.export_service import build_pdf_bytes, render_export_content
from app.services.job_center_service import track_job


def _job_key(job_id: str) -> str:
    return f"{get_settings().outbox_stream_prefix}:exportjob:{job_id}"


def _export_stream() -> str:
    return f"{get_settings().outbox_stream_prefix}:export"


async def enqueue_export_job(
    *,
    design_title: str,
    design_input: DesignInputPayload,
    design_output: DesignOutputPayload,
    export_format: Literal["pdf", "markdown"],
    workspace_id: int | None = None,
    user_id: int | None = None,
    design_id: int | None = None,
) -> str:
    redis = get_redis_client()
    job_id = uuid4().hex
    key = _job_key(job_id)
    await redis.set(
        key,
        json.dumps(
            {
                "job_id": job_id,
                "status": "queued",
                "format": export_format,
                "filename": f"{design_title[:60] or 'design'}.{ 'pdf' if export_format == 'pdf' else 'md'}",
                "workspace_id": workspace_id,
                "user_id": user_id,
                "design_id": design_id,
            }
        ),
        ex=3600,
    )
    if workspace_id is not None and user_id is not None:
        await track_job(
            workspace_id=workspace_id,
            user_id=user_id,
            payload={
                "job_type": "export",
                "job_id": job_id,
                "design_id": design_id,
                "status": "queued",
                "format": export_format,
                "title": design_title,
            },
        )
    await redis.xadd(
        _export_stream(),
        {
            "type": "export.generate",
            "payload_json": json.dumps(
                {"job_id": job_id, "design_title": design_title, "format": export_format, "input": design_input.model_dump(), "output": design_output.model_dump()}
            ),
        },
        maxlen=get_settings().stream_maxlen_approx,
        approximate=True,
    )
    return job_id


async def process_export_job(
    job_id: str,
    *,
    design_title: str,
    design_input: DesignInputPayload,
    design_output: DesignOutputPayload,
    export_format: Literal["pdf", "markdown"],
) -> None:
    redis = get_redis_client()
    key = _job_key(job_id)
    existing = await get_export_job(job_id)
    try:
        await redis.set(
            key,
            json.dumps(
                {
                    "job_id": job_id,
                    "status": "running",
                    "format": export_format,
                    "workspace_id": (existing or {}).get("workspace_id"),
                    "user_id": (existing or {}).get("user_id"),
                    "design_id": (existing or {}).get("design_id"),
                }
            ),
            ex=3600,
        )
        if export_format == "pdf":
            content_bytes = build_pdf_bytes(design_title, design_input, design_output)
            content_b64 = base64.b64encode(content_bytes).decode("ascii")
            mime = "application/pdf"
            filename = f"{design_title[:60] or 'design'}-systemforge.pdf"
        else:
            markdown = render_export_content(
                design_title=design_title,
                design_input=design_input,
                output=design_output,
                export_format="markdown",
            )
            content_b64 = base64.b64encode(markdown.encode("utf-8")).decode("ascii")
            mime = "text/markdown; charset=utf-8"
            filename = f"{design_title[:60] or 'design'}-systemforge.md"
        await redis.set(
            key,
            json.dumps(
                {
                    "job_id": job_id,
                    "status": "completed",
                    "format": export_format,
                    "filename": filename,
                    "mime_type": mime,
                    "content_b64": content_b64,
                    "workspace_id": (existing or {}).get("workspace_id"),
                    "user_id": (existing or {}).get("user_id"),
                    "design_id": (existing or {}).get("design_id"),
                }
            ),
            ex=3600,
        )
    except Exception as exc:
        await redis.set(
            key,
            json.dumps(
                {
                    "job_id": job_id,
                    "status": "failed",
                    "format": export_format,
                    "error": str(exc),
                    "workspace_id": (existing or {}).get("workspace_id"),
                    "user_id": (existing or {}).get("user_id"),
                    "design_id": (existing or {}).get("design_id"),
                }
            ),
            ex=3600,
        )


async def get_export_job(job_id: str) -> dict | None:
    redis = get_redis_client()
    raw = await redis.get(_job_key(job_id))
    if not raw:
        return None
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    return json.loads(raw)

