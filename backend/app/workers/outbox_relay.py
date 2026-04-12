from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.core.config import get_settings
from app.core.redis import get_redis_client
from app.db.session import SessionLocal
from app.messaging import repositories as repo

logger = logging.getLogger("systemforge.outbox")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _stream_for_event(event_type: str) -> str:
    settings = get_settings()
    if event_type in {"message.created", "message.delivered", "message.read"}:
        return f"{settings.outbox_stream_prefix}:delivery"
    return f"{settings.outbox_stream_prefix}:events"


def _next_backoff_seconds(attempts: int) -> int:
    settings = get_settings()
    return min(2 ** max(1, attempts), settings.outbox_relay_max_backoff_seconds)


@dataclass(frozen=True)
class ClaimedOutboxEvent:
    id: int
    aggregate_type: str
    aggregate_id: int
    event_type: str
    payload_json: dict
    created_at: datetime | None
    attempts: int


class OutboxRelayWorker:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.redis = get_redis_client()

    def _claim_batch(self, db, now: datetime) -> list[ClaimedOutboxEvent]:
        events = repo.claim_outbox_events(
            db,
            now=now,
            batch_size=self.settings.outbox_relay_batch_size,
            processing_timeout_seconds=self.settings.outbox_relay_processing_timeout_seconds,
        )
        return [
            ClaimedOutboxEvent(
                id=int(event.id),
                aggregate_type=event.aggregate_type,
                aggregate_id=int(event.aggregate_id),
                event_type=event.event_type,
                payload_json=event.payload_json,
                created_at=event.created_at,
                attempts=int(event.attempts or 0),
            )
            for event in events
        ]

    async def _publish_one(self, event: ClaimedOutboxEvent) -> str:
        stream = _stream_for_event(event.event_type)
        payload = {
            "event_id": str(event.id),
            "event_type": event.event_type,
            "aggregate_type": event.aggregate_type,
            "aggregate_id": str(event.aggregate_id),
            "payload_json": json.dumps(event.payload_json, separators=(",", ":")),
            "created_at": event.created_at.isoformat() if event.created_at else _utcnow().isoformat(),
        }
        return await self.redis.xadd(
            stream,
            payload,
            maxlen=self.settings.stream_maxlen_approx,
            approximate=True,
        )
    async def process_once(self) -> int:
        now = _utcnow()
        with SessionLocal() as db:
            events = self._claim_batch(db, now)
            db.commit()

        if not events:
            return 0

        processed = 0
        for event in events:
            try:
                stream_id = await self._publish_one(event)
                with SessionLocal() as db:
                    marked = repo.mark_outbox_event_published(
                        db,
                        outbox_event_id=event.id,
                        published_at=_utcnow(),
                    )
                    db.commit()
                    if not marked:
                        # Another recovery worker may have already transitioned this row.
                        continue
                processed += 1
                logger.info(
                    "outbox_published",
                    extra={
                        "outbox_event_id": event.id,
                        "event_type": event.event_type,
                        "stream_id": stream_id,
                    },
                )
            except Exception as exc:
                backoff = _next_backoff_seconds(event.attempts or 1)
                with SessionLocal() as db:
                    marked = repo.mark_outbox_event_failed(
                        db,
                        outbox_event_id=event.id,
                        next_attempt_at=_utcnow() + timedelta(seconds=backoff),
                        last_error=str(exc),
                    )
                    db.commit()
                    if not marked:
                        continue
                logger.exception(
                    "outbox_publish_failed",
                    extra={
                        "outbox_event_id": event.id,
                        "event_type": event.event_type,
                        "attempts": int(event.attempts or 0),
                        "retry_in_seconds": backoff,
                    },
                )
        return processed
