import json

import pytest

from app.notifications.service import NotificationService


class FakeRedis:
    def __init__(self):
        self.set_data: dict[str, set[str]] = {}
        self.stream_data: dict[str, list[dict[str, str]]] = {}
        self.zset_data: dict[str, dict[str, int]] = {}

    async def scard(self, key: str):
        return len(self.set_data.get(key, set()))

    async def xadd(self, stream: str, payload: dict[str, str], **kwargs):
        self.stream_data.setdefault(stream, []).append(payload)
        return f"{len(self.stream_data[stream])}-0"

    async def zadd(self, key: str, mapping: dict[str, int]):
        z = self.zset_data.setdefault(key, {})
        z.update(mapping)
        return len(mapping)

    async def zrangebyscore(self, key: str, min: int, max: int, start: int = 0, num: int = 100):
        z = self.zset_data.get(key, {})
        due = [member for member, score in sorted(z.items(), key=lambda x: x[1]) if min <= score <= max]
        return due[start : start + num]

    async def zrem(self, key: str, member: str):
        z = self.zset_data.get(key, {})
        z.pop(member, None)
        return 1

    async def eval(self, script: str, numkeys: int, zset_key: str, stream_key: str, now_ms: str, max_count: str, maxlen: str):
        due = await self.zrangebyscore(zset_key, 0, int(now_ms), 0, int(max_count))
        promoted = 0
        for raw in due:
            try:
                payload = json.loads(raw)
            except Exception:
                await self.zrem(zset_key, raw)
                continue
            await self.xadd(stream_key, payload)
            await self.zrem(zset_key, raw)
            promoted += 1
        return promoted


@pytest.mark.asyncio
async def test_enqueue_delayed_then_promote_due_notification():
    service = NotificationService()
    service.redis = FakeRedis()
    service.settings.outbox_stream_prefix = "sf:rt:v1:stream"

    payload = {
        "message_id": 11,
        "conversation_id": 7,
        "content_json": {"text": "hello"},
    }
    delayed_id = await service.enqueue_notification(
        recipient_user_id=99,
        message_payload=payload,
        attempts=1,
        not_before_ms=9_999_999_999_999,
    )
    assert isinstance(delayed_id, str)
    assert service.redis.stream_data.get("sf:rt:v1:stream:notify") is None

    zset_key = "sf:rt:v1:stream:notify:delayed"
    member = next(iter(service.redis.zset_data[zset_key]))
    loaded = json.loads(member)
    loaded["not_before_ms"] = "1"
    service.redis.zset_data[zset_key] = {json.dumps(loaded, separators=(",", ":")): 1}

    promoted = await service.promote_due_notifications(limit=10)
    assert promoted == 1
    assert len(service.redis.stream_data["sf:rt:v1:stream:notify"]) == 1


@pytest.mark.asyncio
async def test_send_with_mock_providers_requires_registered_tokens_by_default():
    service = NotificationService()
    service.settings.notification_allow_mock_tokens = False
    service.get_active_device_tokens = lambda *, user_id: []  # type: ignore[method-assign]

    results = await service.send_with_mock_providers(
        recipient_user_id=999,
        title="New message",
        body="hello",
        data={"conversation_id": "1", "message_id": "1"},
    )
    assert results == []


@pytest.mark.asyncio
async def test_send_with_mock_providers_allows_fallback_when_enabled():
    service = NotificationService()
    service.settings.notification_allow_mock_tokens = True
    service.get_active_device_tokens = lambda *, user_id: []  # type: ignore[method-assign]

    results = await service.send_with_mock_providers(
        recipient_user_id=42,
        title="New message",
        body="hello",
        data={"conversation_id": "1", "message_id": "1"},
    )
    assert len(results) == 2
    assert {item.provider for item in results} == {"fcm", "apns"}

