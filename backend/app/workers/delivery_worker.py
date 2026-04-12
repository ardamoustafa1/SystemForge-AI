from __future__ import annotations

import json
import logging
import os
import socket
from dataclasses import dataclass
from typing import Any

from app.core.config import get_settings
from app.core.redis import get_redis_client
from app.db.session import SessionLocal
from app.messaging import repositories as msg_repo
from app.notifications.service import notification_service
from app.realtime.presence_service import presence_service

logger = logging.getLogger("systemforge.delivery")


def _delivery_stream() -> str:
    return f"{get_settings().outbox_stream_prefix}:delivery"


def _realtime_user_stream(user_id: int) -> str:
    return f"{get_settings().outbox_stream_prefix}:realtime:{user_id}"


@dataclass(frozen=True)
class MessageCreatedEventPayload:
    message_id: int
    conversation_id: int
    sender_user_id: int
    recipient_user_ids: list[int]
    content_type: str
    content_json: dict[str, Any]
    created_at: str
    server_seq: int


class DeliveryWorker:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.redis = get_redis_client()
        self.group = self.settings.delivery_consumer_group
        self.consumer = f"{self.settings.delivery_consumer_name}-{socket.gethostname()}-{os.getpid()}"

    async def _ensure_group(self) -> None:
        stream = _delivery_stream()
        try:
            await self.redis.xgroup_create(name=stream, groupname=self.group, id="0", mkstream=True)
        except Exception as exc:
            # BUSYGROUP is expected on restart.
            if "BUSYGROUP" not in str(exc):
                raise

    async def _recipient_active(self, user_id: int) -> bool:
        # Prefer worker-local Redis to keep presence checks consistent in tests and multi-instance workers.
        local_count = await self.redis.scard(f"sf:rt:v1:user:sockets:{user_id}")
        if int(local_count or 0) > 0:
            return True
        return await presence_service.active_socket_count(user_id=user_id) > 0

    async def _dispatch_to_active_user(self, *, user_id: int, message_payload: dict[str, Any]) -> str:
        stream = _realtime_user_stream(user_id)
        return await self.redis.xadd(
            stream,
            {
                "type": "message.new",
                "payload_json": json.dumps(message_payload, separators=(",", ":")),
            },
            maxlen=self.settings.stream_maxlen_approx,
            approximate=True,
        )

    def _recipient_dedupe_key(self, *, message_id: int, recipient_user_id: int) -> str:
        return f"sf:rt:v1:delivery:done:{message_id}:{recipient_user_id}"

    def _parse_message_created_payload(self, fields: dict[str, str]) -> MessageCreatedEventPayload | None:
        try:
            payload_json = fields.get("payload_json", "{}")
            payload = json.loads(payload_json)
            recipients_raw = payload.get("recipient_user_ids", [])
            if not isinstance(recipients_raw, list):
                return None
            recipients: list[int] = []
            for user_id in recipients_raw:
                value = int(user_id)
                if value > 0:
                    recipients.append(value)
            message_id = int(payload.get("message_id", 0) or 0)
            conversation_id = int(payload.get("conversation_id", 0) or 0)
            sender_user_id = int(payload.get("sender_user_id", 0) or 0)
            server_seq = int(payload.get("server_seq", -1) or -1)
            content_type = str(payload.get("content_type", "text"))
            content_json = payload.get("content_json", {})
            if (
                message_id <= 0
                or conversation_id <= 0
                or sender_user_id <= 0
                or server_seq < 0
                or not isinstance(content_json, dict)
            ):
                return None
            return MessageCreatedEventPayload(
                message_id=message_id,
                conversation_id=conversation_id,
                sender_user_id=sender_user_id,
                recipient_user_ids=recipients,
                content_type=content_type,
                content_json=content_json,
                created_at=str(payload.get("created_at", "")),
                server_seq=server_seq,
            )
        except Exception:
            return None

    async def _on_delivery_dispatched(
        self,
        *,
        payload: MessageCreatedEventPayload,
        recipient_user_id: int,
    ) -> None:
        try:
            from app.messaging.service import acknowledge_delivered
            with SessionLocal() as db:
                acknowledge_delivered(db, message_id=payload.message_id, recipient_user_id=recipient_user_id)
        except Exception:
            pass

        logger.debug(
            "delivery_dispatched_candidate",
            extra={
                "message_id": payload.message_id,
                "conversation_id": payload.conversation_id,
                "recipient_user_id": recipient_user_id,
                "server_seq": payload.server_seq,
            },
        )

    @staticmethod
    def _to_message_new_payload(payload: MessageCreatedEventPayload) -> dict[str, Any]:
        return {
            "message_id": payload.message_id,
            "conversation_id": payload.conversation_id,
            "sender_user_id": payload.sender_user_id,
            "recipient_user_ids": payload.recipient_user_ids,
            "content_type": payload.content_type,
            "content_json": payload.content_json,
            "created_at": payload.created_at,
            "server_seq": payload.server_seq,
        }

    async def _process_event(self, event_id: str, fields: dict[str, str]) -> None:
        event_type = fields.get("event_type", "")
        if event_type == "message.created":
            payload = self._parse_message_created_payload(fields)
            if payload is None:
                logger.warning("delivery_invalid_payload", extra={"event_id": event_id})
                await self.redis.xack(_delivery_stream(), self.group, event_id)
                return

            for recipient in payload.recipient_user_ids:
                dedupe_key = self._recipient_dedupe_key(message_id=payload.message_id, recipient_user_id=recipient)
                if await self.redis.exists(dedupe_key):
                    continue
                try:
                    if await self._recipient_active(recipient):
                        await self._dispatch_to_active_user(
                            user_id=recipient,
                            message_payload=self._to_message_new_payload(payload),
                        )
                    else:
                        await notification_service.enqueue_notification(
                            recipient_user_id=recipient,
                            message_payload=self._to_message_new_payload(payload),
                            attempts=0,
                        )
                    await self.redis.setex(
                        dedupe_key,
                        self.settings.delivery_recipient_dedupe_ttl_seconds,
                        "1",
                    )
                    await self._on_delivery_dispatched(payload=payload, recipient_user_id=recipient)
                except Exception:
                    logger.exception(
                        "delivery_dispatch_failed",
                        extra={"event_id": event_id, "recipient_user_id": recipient},
                    )
                    # Don't ack on dispatch failures to allow retry by pending entries.
                    return

            await self.redis.xack(_delivery_stream(), self.group, event_id)
            return

        if event_type in {"message.delivered", "message.read"}:
            try:
                payload = json.loads(fields.get("payload_json", "{}"))
            except Exception:
                payload = {}
            conversation_id = int(payload.get("conversation_id", 0) or 0)
            if conversation_id <= 0:
                await self.redis.xack(_delivery_stream(), self.group, event_id)
                return
            with SessionLocal() as db:
                member_ids = msg_repo.list_active_member_ids(db, conversation_id=conversation_id)
            if event_type == "message.delivered":
                actor_user_id = int(payload.get("recipient_user_id", 0) or 0)
                outgoing_type = "delivery.updated"
            else:
                actor_user_id = int(payload.get("reader_user_id", 0) or 0)
                outgoing_type = "read.updated"

            for member_id in member_ids:
                if member_id == actor_user_id:
                    continue
                try:
                    await self.redis.xadd(
                        _realtime_user_stream(member_id),
                        {
                            "type": outgoing_type,
                            "payload_json": json.dumps(payload, separators=(",", ":")),
                        },
                        maxlen=self.settings.stream_maxlen_approx,
                        approximate=True,
                    )
                except Exception:
                    logger.exception(
                        "delivery_state_fanout_failed",
                        extra={"event_id": event_id, "target_user_id": member_id, "event_type": event_type},
                    )
                    return
            await self.redis.xack(_delivery_stream(), self.group, event_id)
            return

        # Ignore unsupported event types in delivery stream.
        logger.debug("delivery_unsupported_event", extra={"event_id": event_id, "event_type": event_type})
        await self.redis.xack(_delivery_stream(), self.group, event_id)
        return

    async def process_once(self) -> int:
        await self._ensure_group()
        stream = _delivery_stream()
        entries = []
        reclaimed = await self.redis.xautoclaim(
            name=stream,
            groupname=self.group,
            consumername=self.consumer,
            min_idle_time=self.settings.delivery_pending_idle_ms,
            start_id="0-0",
            count=self.settings.delivery_batch_size,
        )
        reclaimed_entries = reclaimed[1] if reclaimed else []
        if reclaimed_entries:
            entries = [(stream, reclaimed_entries)]
        else:
            entries = await self.redis.xreadgroup(
                groupname=self.group,
                consumername=self.consumer,
                streams={stream: ">"},
                count=self.settings.delivery_batch_size,
                block=self.settings.delivery_poll_block_ms,
            )
        if not entries:
            return 0

        processed = 0
        for _, stream_entries in entries:
            for event_id, fields in stream_entries:
                await self._process_event(event_id, fields)
                processed += 1
        return processed
