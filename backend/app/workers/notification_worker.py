from __future__ import annotations

import json
import logging
import os
import socket
from datetime import datetime, timezone

from app.core.config import get_settings
from app.core.redis import get_redis_client
from app.notifications.service import notification_service

logger = logging.getLogger("systemforge.notifications.worker")


def _now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def _retry_delay_seconds(attempts: int) -> int:
    settings = get_settings()
    return min(settings.notification_retry_base_seconds * (2 ** max(0, attempts)), 300)


class NotificationWorker:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.redis = get_redis_client()
        self.stream = f"{self.settings.outbox_stream_prefix}:notify"
        self.group = self.settings.notification_consumer_group
        self.consumer = f"{self.settings.notification_consumer_name}-{socket.gethostname()}-{os.getpid()}"

    async def _ensure_group(self) -> None:
        try:
            await self.redis.xgroup_create(name=self.stream, groupname=self.group, id="0", mkstream=True)
        except Exception as exc:
            if "BUSYGROUP" not in str(exc):
                raise

    async def _retry(self, *, recipient_user_id: int, payload: dict, attempts: int) -> None:
        delay_s = _retry_delay_seconds(attempts)
        await notification_service.enqueue_notification(
            recipient_user_id=recipient_user_id,
            message_payload=payload,
            attempts=attempts + 1,
            not_before_ms=_now_ms() + (delay_s * 1000),
        )

    async def _process_entry(self, entry_id: str, fields: dict[str, str]) -> None:
        try:
            recipient_user_id = int(fields.get("recipient_user_id", "0"))
            attempts = int(fields.get("attempts", "0"))
            not_before_ms = int(fields.get("not_before_ms", "0"))
            payload = json.loads(fields.get("payload_json", "{}"))
        except Exception:
            logger.exception("notify_invalid_entry", extra={"entry_id": entry_id})
            await self.redis.xack(self.stream, self.group, entry_id)
            return

        if recipient_user_id <= 0:
            await self.redis.xack(self.stream, self.group, entry_id)
            return

        if not_before_ms > _now_ms():
            await notification_service.enqueue_notification(
                recipient_user_id=recipient_user_id,
                message_payload=payload,
                attempts=attempts,
                not_before_ms=not_before_ms,
            )
            await self.redis.xack(self.stream, self.group, entry_id)
            return

        # User became online while queued: drop push and ack.
        if not await notification_service.is_user_offline(user_id=recipient_user_id):
            await self.redis.xack(self.stream, self.group, entry_id)
            return

        title = "New message"
        body = str(payload.get("content_json", {}).get("text", "You have a new message"))
        if len(body) > 120:
            body = body[:117] + "..."
        results = await notification_service.send_with_mock_providers(
            recipient_user_id=recipient_user_id,
            title=title,
            body=body,
            data={
                "message_id": str(payload.get("message_id", "")),
                "conversation_id": str(payload.get("conversation_id", "")),
            },
        )
        if not results:
            logger.info(
                "notify_no_active_device_tokens",
                extra={"entry_id": entry_id, "recipient_user_id": recipient_user_id},
            )
            await self.redis.xack(self.stream, self.group, entry_id)
            return

        attempt_no = attempts + 1
        for result in results:
            notification_service.record_attempt(
                recipient_user_id=recipient_user_id,
                message_payload=payload,
                provider=result.provider,
                token=result.token,
                success=result.ok,
                attempt_no=attempt_no,
                error_code=result.error,
                error_message=result.error,
            )
        ok = any(result.ok for result in results)
        if ok:
            await self.redis.xack(self.stream, self.group, entry_id)
            return

        if attempts + 1 >= self.settings.notification_max_attempts:
            logger.error(
                "notify_max_attempts_exceeded",
                extra={
                    "entry_id": entry_id,
                    "recipient_user_id": recipient_user_id,
                    "attempts": attempts + 1,
                },
            )
            await self.redis.xack(self.stream, self.group, entry_id)
            return

        await self._retry(recipient_user_id=recipient_user_id, payload=payload, attempts=attempts)
        await self.redis.xack(self.stream, self.group, entry_id)

    async def process_once(self) -> int:
        await self._ensure_group()
        await notification_service.promote_due_notifications(limit=self.settings.notification_batch_size)

        entries = []
        reclaimed = await self.redis.xautoclaim(
            name=self.stream,
            groupname=self.group,
            consumername=self.consumer,
            min_idle_time=self.settings.notification_pending_idle_ms,
            start_id="0-0",
            count=self.settings.notification_batch_size,
        )
        reclaimed_entries = reclaimed[1] if reclaimed else []
        if reclaimed_entries:
            entries = [(self.stream, reclaimed_entries)]
        else:
            entries = await self.redis.xreadgroup(
                groupname=self.group,
                consumername=self.consumer,
                streams={self.stream: ">"},
                count=self.settings.notification_batch_size,
                block=self.settings.notification_poll_block_ms,
            )
        if not entries:
            return 0
        processed = 0
        for _, stream_entries in entries:
            for entry_id, fields in stream_entries:
                await self._process_entry(entry_id, fields)
                processed += 1
        return processed
