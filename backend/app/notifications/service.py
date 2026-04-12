from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from app.core.config import get_settings
from app.core.redis import get_redis_client
from app.db.session import SessionLocal
from app.models.notification import NotificationAttempt, NotificationDevice
from app.notifications.providers import MockPushProvider, NotificationResult, PushProvider, WebhookPushProvider
from app.realtime.presence_service import presence_service


def _now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


class NotificationService:
    def __init__(self, provider: PushProvider | None = None) -> None:
        self.settings = get_settings()
        self.redis = get_redis_client()
        if provider is not None:
            self.provider = provider
        elif self.settings.notification_provider_mode.lower() == "webhook":
            self.provider = WebhookPushProvider(
                fcm_url=self.settings.notification_fcm_webhook_url,
                apns_url=self.settings.notification_apns_webhook_url,
                timeout_seconds=self.settings.notification_provider_timeout_seconds,
            )
        else:
            self.provider = MockPushProvider()

    def _notify_stream(self) -> str:
        return f"{self.settings.outbox_stream_prefix}:notify"

    def _notify_delayed_zset(self) -> str:
        return f"{self.settings.outbox_stream_prefix}:notify:delayed"

    async def is_user_offline(self, *, user_id: int) -> bool:
        return not await presence_service.is_online(user_id=user_id)

    def get_active_device_tokens(self, *, user_id: int) -> list[tuple[str, str]]:
        with SessionLocal() as db:
            rows = (
                db.query(NotificationDevice.provider, NotificationDevice.device_token)
                .filter(
                    NotificationDevice.user_id == user_id,
                    NotificationDevice.is_active.is_(True),
                )
                .all()
            )
            return [(str(provider), str(token)) for provider, token in rows]

    def record_attempt(
        self,
        *,
        recipient_user_id: int,
        message_payload: dict[str, Any],
        provider: str,
        token: str,
        success: bool,
        attempt_no: int,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> None:
        with SessionLocal() as db:
            db.add(
                NotificationAttempt(
                    recipient_user_id=recipient_user_id,
                    message_id=int(message_payload.get("message_id")) if message_payload.get("message_id") else None,
                    conversation_id=(
                        int(message_payload.get("conversation_id")) if message_payload.get("conversation_id") else None
                    ),
                    provider=provider,
                    device_token=token,
                    success=success,
                    attempt_no=attempt_no,
                    error_code=error_code,
                    error_message=error_message,
                )
            )
            db.commit()

    async def enqueue_notification(
        self,
        *,
        recipient_user_id: int,
        message_payload: dict[str, Any],
        attempts: int = 0,
        not_before_ms: int | None = None,
    ) -> str:
        due_ms = int(not_before_ms or _now_ms())
        entry = {
            "recipient_user_id": str(recipient_user_id),
            "message_id": str(message_payload.get("message_id", "")),
            "conversation_id": str(message_payload.get("conversation_id", "")),
            "attempts": str(attempts),
            "not_before_ms": str(due_ms),
            "payload_json": json.dumps(message_payload, separators=(",", ":")),
        }
        if due_ms > _now_ms():
            payload_key = json.dumps(entry, separators=(",", ":"))
            await self.redis.zadd(self._notify_delayed_zset(), {payload_key: due_ms})
            return payload_key
        return await self.redis.xadd(
            self._notify_stream(),
            entry,
            maxlen=self.settings.stream_maxlen_approx,
            approximate=True,
        )

    async def promote_due_notifications(self, *, limit: int = 100) -> int:
        now_ms = _now_ms()
        zset_key = self._notify_delayed_zset()
        script = """
local zset_key = KEYS[1]
local stream_key = KEYS[2]
local now_ms = tonumber(ARGV[1])
local max_count = tonumber(ARGV[2])
local maxlen = tonumber(ARGV[3])
local entries = redis.call('ZRANGEBYSCORE', zset_key, '-inf', now_ms, 'LIMIT', 0, max_count)
local promoted = 0
for _, raw in ipairs(entries) do
  local ok, payload = pcall(cjson.decode, raw)
  if ok and payload then
    redis.call(
      'XADD',
      stream_key,
      'MAXLEN',
      '~',
      maxlen,
      '*',
      'recipient_user_id', tostring(payload['recipient_user_id'] or ''),
      'message_id', tostring(payload['message_id'] or ''),
      'conversation_id', tostring(payload['conversation_id'] or ''),
      'attempts', tostring(payload['attempts'] or '0'),
      'not_before_ms', tostring(payload['not_before_ms'] or '0'),
      'payload_json', tostring(payload['payload_json'] or '{}')
    )
    promoted = promoted + 1
  end
  redis.call('ZREM', zset_key, raw)
end
return promoted
"""
        promoted = await self.redis.eval(
            script,
            2,
            zset_key,
            self._notify_stream(),
            str(now_ms),
            str(limit),
            str(self.settings.stream_maxlen_approx),
        )
        return int(promoted or 0)

    async def enqueue_if_offline(self, *, recipient_user_id: int, message_payload: dict[str, Any]) -> bool:
        if not await self.is_user_offline(user_id=recipient_user_id):
            return False
        await self.enqueue_notification(
            recipient_user_id=recipient_user_id,
            message_payload=message_payload,
            attempts=0,
        )
        return True

    async def send_with_mock_providers(
        self,
        *,
        recipient_user_id: int,
        title: str,
        body: str,
        data: dict[str, Any],
    ) -> list[NotificationResult]:
        tokens = self.get_active_device_tokens(user_id=recipient_user_id)
        if not tokens:
            if not self.settings.notification_allow_mock_tokens:
                return []
            tokens = [("fcm", f"mock-fcm-{recipient_user_id}"), ("apns", f"mock-apns-{recipient_user_id}")]

        results: list[NotificationResult] = []
        for provider, token in tokens:
            if provider == "fcm":
                results.append(await self.provider.send_fcm(token=token, title=title, body=body, data=data))
            elif provider == "apns":
                results.append(await self.provider.send_apns(token=token, title=title, body=body, data=data))
        return results


notification_service = NotificationService()
