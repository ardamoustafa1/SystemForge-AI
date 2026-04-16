from __future__ import annotations

import json
import logging
import os
import socket
from datetime import datetime, timezone
from uuid import uuid4

from app.core.config import get_settings
from app.core.redis import get_redis_client
from app.db.session import SessionLocal
from app.services.generation_service import generate_structured_design
from app.models import Design, DesignOutput, DesignInput, DesignOutputVersion
from app.schemas.design import DesignInputPayload
from app.services.export_service import build_markdown_export
from app.core.metrics import observe_worker_event, set_worker_queue_lag, observe_worker_retry

logger = logging.getLogger("systemforge.generation")

def _generation_stream() -> str:
    return f"{get_settings().outbox_stream_prefix}:generation"

class GenerationWorker:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.redis = get_redis_client()
        self.group = self.settings.generation_consumer_group
        self.consumer = f"{self.settings.generation_consumer_name}-{socket.gethostname()}-{os.getpid()}"

    async def _ensure_group(self) -> None:
        stream = _generation_stream()
        try:
            await self.redis.xgroup_create(name=stream, groupname=self.group, id="0", mkstream=True)
        except Exception as exc:
            if "BUSYGROUP" not in str(exc):
                raise

    async def _emit_design_event(self, user_id: int, event_type: str, payload: dict[str, object]) -> None:
        stream_route = f"{self.settings.outbox_stream_prefix}:realtime:{user_id}"
        await self.redis.xadd(
            stream_route,
            {
                "type": event_type,
                "payload_json": json.dumps(payload),
            },
            maxlen=self.settings.stream_maxlen_approx,
            approximate=True,
        )

    async def _process_event(self, event_id: str, fields: dict[str, str]) -> None:
        try:
            payload_json = fields.get("payload_json", "{}")
            payload = json.loads(payload_json)
            design_id = int(payload.get("design_id", 0))
            scale_stance = payload.get("scale_stance", "balanced")
            output_language = payload.get("output_language", "en")
            trace_id = payload.get("trace_id") or str(uuid4())
            if design_id <= 0:
                await self.redis.xack(_generation_stream(), self.group, event_id)
                return

            with SessionLocal() as db:
                design = db.query(Design).filter(Design.id == design_id).first()
                if not design:
                    await self.redis.xack(_generation_stream(), self.group, event_id)
                    return
                if design.status == "completed":
                    await self.redis.xack(_generation_stream(), self.group, event_id)
                    return

                design_input = db.query(DesignInput).filter(DesignInput.design_id == design_id).first()
                if not design_input:
                    await self.redis.xack(_generation_stream(), self.group, event_id)
                    return
                input_payload = DesignInputPayload.model_validate(design_input.payload)
                user_id = design.owner_id

            try:
                await self._emit_design_event(
                    user_id,
                    "design.progress",
                    {"design_id": design_id, "status": "generating", "phase": "context_parsed", "progress_pct": 15, "trace_id": trace_id},
                )
            except Exception:
                logger.debug("generation_worker_progress_emit_failed", extra={"design_id": design_id, "phase": "context_parsed"})

            logger.info("generation_worker_starting_generation", extra={"design_id": design_id})
            observe_worker_event("generation", "started")
            output_payload, generation_ms, model_name = await generate_structured_design(
                input_payload, scale_stance=scale_stance, output_language=output_language
            )
            try:
                await self._emit_design_event(
                    user_id,
                    "design.progress",
                    {"design_id": design_id, "status": "generating", "phase": "architecture_designed", "progress_pct": 65, "trace_id": trace_id},
                )
            except Exception:
                logger.debug("generation_worker_progress_emit_failed", extra={"design_id": design_id, "phase": "architecture_designed"})
            
            markdown_export = build_markdown_export(input_payload.project_title, input_payload, output_payload)
            try:
                await self._emit_design_event(
                    user_id,
                    "design.progress",
                    {"design_id": design_id, "status": "generating", "phase": "finalizing", "progress_pct": 90, "trace_id": trace_id},
                )
            except Exception:
                logger.debug("generation_worker_progress_emit_failed", extra={"design_id": design_id, "phase": "finalizing"})

            with SessionLocal() as db:
                design = db.query(Design).filter(Design.id == design_id).first()
                if not design:
                    await self.redis.xack(_generation_stream(), self.group, event_id)
                    return

                existing_output = db.query(DesignOutput).filter(DesignOutput.design_id == design_id).first()
                if not existing_output:
                    existing_output = DesignOutput(
                        design_id=design.id,
                        payload=output_payload.model_dump(),
                        markdown_export=markdown_export,
                        model_name=model_name,
                        generation_ms=generation_ms,
                    )
                    db.add(existing_output)
                else:
                    db.add(DesignOutputVersion(
                        design_id=design.id,
                        payload=dict(existing_output.payload),
                        markdown_export=existing_output.markdown_export,
                        model_name=existing_output.model_name,
                        generation_ms=existing_output.generation_ms,
                        scale_stance=scale_stance,
                    ))
                    existing_output.payload = output_payload.model_dump()
                    existing_output.markdown_export = markdown_export
                    existing_output.model_name = model_name
                    existing_output.generation_ms = generation_ms
                
                design.status = "completed"
                design.updated_at = datetime.now(timezone.utc)
                db.commit()
                db.refresh(design)
                user_id = design.owner_id

            logger.info("generation_worker_completed_generation", extra={"design_id": design_id})
            observe_worker_event("generation", "completed")

            # Broadcast realtime update so UI can magically refresh
            try:
                await self._emit_design_event(
                    user_id,
                    "design.updated",
                    {"design_id": design_id, "status": "completed", "phase": "completed", "progress_pct": 100, "trace_id": trace_id},
                )
            except Exception:
                pass

            await self.redis.xack(_generation_stream(), self.group, event_id)

        except Exception:
            logger.exception("generation_worker_event_error")
            observe_worker_event("generation", "failed")
            observe_worker_retry("generation", 1)
            try:
                payload_json = fields.get("payload_json", "{}")
                payload = json.loads(payload_json)
                design_id = int(payload.get("design_id", 0))
                if design_id > 0:
                    with SessionLocal() as db:
                        design = db.query(Design).filter(Design.id == design_id).first()
                        if design and design.status == "generating":
                            design.status = "failed"
                            design.updated_at = datetime.now(timezone.utc)
                            db.commit()
                            db.refresh(design)
                            user_id = design.owner_id
                            trace_id = payload.get("trace_id") or str(uuid4())
                            await self._emit_design_event(
                                user_id,
                                "design.updated",
                                {"design_id": design_id, "status": "failed", "phase": "failed", "trace_id": trace_id},
                            )
            except Exception:
                pass
            finally:
                await self.redis.xack(_generation_stream(), self.group, event_id)

    async def process_once(self) -> int:
        await self._ensure_group()
        stream = _generation_stream()
        processed: int = 0

        # Autoclaim entries that have been pending for more than 60 seconds
        try:
            res = await self.redis.xautoclaim(
                stream,
                self.group,
                self.consumer,
                min_idle_time=60000,
                start_id="0",
                count=self.settings.generation_batch_size,
            )
            # handle both redis-py 4/5 return types
            claimed_entries = res[1] if isinstance(res, tuple) and len(res) >= 2 else []
            for event_id, fields in claimed_entries:
                await self._process_event(event_id, fields)
                processed += 1
        except Exception:
            logger.exception("generation_worker_autoclaim_error")

        entries = await self.redis.xreadgroup(
            groupname=self.group,
            consumername=self.consumer,
            streams={stream: ">"},
            count=self.settings.generation_batch_size,
            block=self.settings.generation_poll_block_ms,
        )
        if not entries:
            set_worker_queue_lag("generation", 0)
            return processed
            
        for _, stream_entries in entries:
            set_worker_queue_lag("generation", float(len(stream_entries)))
            for event_id, fields in stream_entries:
                await self._process_event(event_id, fields)
                processed = processed + 1  # type: ignore  # type: ignore
        return processed
