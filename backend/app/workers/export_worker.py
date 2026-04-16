from __future__ import annotations

import json
import logging
import os
import socket

from app.core.config import get_settings
from app.core.redis import get_redis_client
from app.schemas.design import DesignInputPayload, DesignOutputPayload
from app.services.export_job_service import process_export_job
from app.core.metrics import observe_worker_event, set_worker_queue_lag, observe_worker_retry

logger = logging.getLogger("systemforge.export")


def _export_stream() -> str:
    return f"{get_settings().outbox_stream_prefix}:export"


class ExportWorker:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.redis = get_redis_client()
        self.group = self.settings.export_consumer_group
        self.consumer = f"{self.settings.export_consumer_name}-{socket.gethostname()}-{os.getpid()}"

    async def _ensure_group(self) -> None:
        stream = _export_stream()
        try:
            await self.redis.xgroup_create(name=stream, groupname=self.group, id="0", mkstream=True)
        except Exception as exc:
            if "BUSYGROUP" not in str(exc):
                raise

    async def _process_event(self, event_id: str, fields: dict[str, str]) -> None:
        try:
            observe_worker_event("export", "received")
            payload = json.loads(fields.get("payload_json", "{}"))
            if payload.get("type") == "export.generate":
                # tolerate future envelope nesting
                payload = payload.get("payload", {})
            job_id = str(payload.get("job_id", "")).strip()
            design_title = str(payload.get("design_title", "design"))
            export_format = str(payload.get("format", "pdf"))
            raw_input = payload.get("input", {})
            raw_output = payload.get("output", {})
            if not job_id:
                await self.redis.xack(_export_stream(), self.group, event_id)
                return
            parsed_input = DesignInputPayload.model_validate(raw_input)
            parsed_output = DesignOutputPayload.model_validate(raw_output)
            await process_export_job(
                job_id,
                design_title=design_title,
                design_input=parsed_input,
                design_output=parsed_output,
                export_format=export_format,  # type: ignore[arg-type]
            )
            await self.redis.xack(_export_stream(), self.group, event_id)
            observe_worker_event("export", "completed")
        except Exception:
            logger.exception("export_worker_event_error")
            observe_worker_event("export", "failed")
            observe_worker_retry("export", 1)
            await self.redis.xack(_export_stream(), self.group, event_id)

    async def process_once(self) -> int:
        await self._ensure_group()
        stream = _export_stream()
        entries = await self.redis.xreadgroup(
            groupname=self.group,
            consumername=self.consumer,
            streams={stream: ">"},
            count=self.settings.export_batch_size,
            block=self.settings.export_poll_block_ms,
        )
        if not entries:
            set_worker_queue_lag("export", 0)
            return 0
        processed = 0
        for _, stream_entries in entries:
            set_worker_queue_lag("export", float(len(stream_entries)))
            for event_id, fields in stream_entries:
                await self._process_event(event_id, fields)
                processed += 1
        return processed

