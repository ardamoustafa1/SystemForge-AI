import json

import pytest

from app.notifications.service import notification_service
from app.realtime.presence_service import presence_service
from app.workers.delivery_worker import DeliveryWorker
from app.workers.notification_worker import NotificationWorker


class FakeRedis:
    def __init__(self):
        self.set_data: dict[str, set[str]] = {}
        self.stream_data: dict[str, list[tuple[str, dict[str, str]]]] = {}
        self.zset_data: dict[str, dict[str, int]] = {}
        self.acked: list[tuple[str, str, str]] = []
        self._id = 0

    async def ping(self):
        return True

    async def exists(self, key: str):
        return int(key in self.stream_data or key in self.set_data)

    async def setex(self, key: str, ttl: int, value: str):
        return True

    async def sadd(self, key: str, value: str):
        self.set_data.setdefault(key, set()).add(value)
        return 1

    async def scard(self, key: str):
        return len(self.set_data.get(key, set()))

    async def hgetall(self, key: str):
        return {}

    async def xgroup_create(self, name: str, groupname: str, id: str, mkstream: bool = True):
        self.stream_data.setdefault(name, [])
        return True

    async def xautoclaim(self, **kwargs):
        return ("0-0", [], [])

    async def xreadgroup(self, **kwargs):
        return []

    async def xadd(self, stream: str, payload: dict[str, str], **kwargs):
        self._id += 1
        event_id = f"{self._id}-0"
        self.stream_data.setdefault(stream, []).append((event_id, payload))
        return event_id

    async def xack(self, stream: str, group: str, event_id: str):
        self.acked.append((stream, group, event_id))
        return 1

    async def zadd(self, key: str, mapping: dict[str, int]):
        z = self.zset_data.setdefault(key, {})
        z.update(mapping)
        return len(mapping)

    async def zrangebyscore(self, key: str, min: int, max: int, start: int = 0, num: int = 100):
        z = self.zset_data.get(key, {})
        members = [m for m, score in sorted(z.items(), key=lambda x: x[1]) if min <= score <= max]
        return members[start : start + num]

    async def zrem(self, key: str, member: str):
        self.zset_data.get(key, {}).pop(member, None)
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
async def test_delivery_to_notify_retry_promotion_flow(monkeypatch):
    fake = FakeRedis()

    delivery = DeliveryWorker()
    delivery.redis = fake
    notification = NotificationWorker()
    notification.redis = fake
    notification_service.redis = fake
    presence_service.redis = fake

    # Force recipient offline (no socket set)
    payload = {
        "message_id": 222,
        "conversation_id": 8,
        "sender_user_id": 99,
        "recipient_user_ids": [77],
        "content_type": "text",
        "content_json": {"text": "hello offline"},
        "created_at": "2026-01-01T00:00:00+00:00",
        "server_seq": 1,
    }
    fields = {"event_type": "message.created", "payload_json": json.dumps(payload)}
    await delivery._process_event("10-0", fields)

    notify_stream = f"{notification.settings.outbox_stream_prefix}:notify"
    entry_id, entry_fields = fake.stream_data[notify_stream][0]

    async def always_fail(**kwargs):
        class R:
            ok = False
            provider = "fcm"
            token = "mock-fcm-token"
            error = "mock_failure"

        return [R(), R()]

    monkeypatch.setattr(notification_service, "send_with_mock_providers", always_fail)
    monkeypatch.setattr(notification_service, "record_attempt", lambda **kwargs: None)
    await notification._process_entry(entry_id, entry_fields)

    delayed_key = f"{notification.settings.outbox_stream_prefix}:notify:delayed"
    assert len(fake.zset_data.get(delayed_key, {})) == 1

    # Make delayed entry due now and promote.
    member = next(iter(fake.zset_data[delayed_key].keys()))
    fake.zset_data[delayed_key][member] = 0
    promoted = await notification_service.promote_due_notifications(limit=10)
    assert promoted == 1
    assert len(fake.stream_data[notify_stream]) >= 2
