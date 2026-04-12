import json

import pytest

from app.messaging.models import Conversation, ConversationMember
from app.models.user import User
from app.workers.delivery_worker import DeliveryWorker
from conftest import TestingSessionLocal


class FakeRedis:
    def __init__(self):
        self.keys: dict[str, str] = {}
        self.stream_entries: list[tuple[str, dict]] = []
        self.acks: list[tuple[str, str, str]] = []
        self.online_users: set[int] = set()

    async def exists(self, key: str):
        return int(key in self.keys)

    async def setex(self, key: str, ttl: int, value: str):
        self.keys[key] = value
        return True

    async def scard(self, key: str):
        try:
            user_id = int(key.rsplit(":", 1)[1])
        except Exception:
            return 0
        return 1 if user_id in self.online_users else 0

    async def xadd(self, stream: str, payload: dict, **kwargs):
        self.stream_entries.append((stream, payload))
        return "1-0"

    async def xack(self, stream: str, group: str, event_id: str):
        self.acks.append((stream, group, event_id))
        return 1


@pytest.mark.asyncio
async def test_delivery_worker_recipient_dedupe(monkeypatch):
    worker = DeliveryWorker()
    fake = FakeRedis()
    fake.online_users = {20}
    worker.redis = fake

    queued_notifications: list[tuple[int, dict]] = []

    async def fake_enqueue_notification(*, recipient_user_id: int, message_payload: dict, attempts: int = 0, not_before_ms=None):
        queued_notifications.append((recipient_user_id, message_payload))
        return "q-1"

    monkeypatch.setattr("app.workers.delivery_worker.notification_service.enqueue_notification", fake_enqueue_notification)

    payload = {
        "message_id": 101,
        "conversation_id": 5,
        "sender_user_id": 10,
        "recipient_user_ids": [20, 30],
        "content_type": "text",
        "content_json": {"text": "hello"},
        "created_at": "2026-01-01T00:00:00+00:00",
        "server_seq": 1,
    }
    fields = {
        "event_type": "message.created",
        "payload_json": json.dumps(payload),
    }

    await worker._process_event("1-0", fields)
    await worker._process_event("1-0", fields)

    # Active recipient gets dispatched only once due to dedupe key.
    realtime_stream_writes = [x for x in fake.stream_entries if ":realtime:20" in x[0]]
    assert len(realtime_stream_writes) == 1
    # Offline recipient enqueue also only once.
    assert len(queued_notifications) == 1


@pytest.mark.asyncio
async def test_delivery_worker_fanout_delivery_and_read_updates(monkeypatch):
    with TestingSessionLocal() as db:
        db.add_all(
            [
                User(id=201, email="u201@test.dev", full_name="u201", password_hash="x", is_active=True),
                User(id=202, email="u202@test.dev", full_name="u202", password_hash="x", is_active=True),
                User(id=203, email="u203@test.dev", full_name="u203", password_hash="x", is_active=True),
            ]
        )
        db.add(Conversation(id=9001, kind="group", created_by_user_id=201))
        db.add_all(
            [
                ConversationMember(conversation_id=9001, user_id=201, role="owner"),
                ConversationMember(conversation_id=9001, user_id=202, role="member"),
                ConversationMember(conversation_id=9001, user_id=203, role="member"),
            ]
        )
        db.commit()

    worker = DeliveryWorker()
    fake = FakeRedis()
    worker.redis = fake
    monkeypatch.setattr("app.workers.delivery_worker.SessionLocal", TestingSessionLocal)

    delivered_fields = {
        "event_type": "message.delivered",
        "payload_json": json.dumps(
            {
                "message_id": 501,
                "conversation_id": 9001,
                "recipient_user_id": 202,
                "server_seq": 8,
                "delivered_at": "2026-01-01T00:00:00+00:00",
            }
        ),
    }
    await worker._process_event("d-1", delivered_fields)

    read_fields = {
        "event_type": "message.read",
        "payload_json": json.dumps(
            {
                "conversation_id": 9001,
                "reader_user_id": 203,
                "read_upto_server_seq": 8,
                "read_message_id": 501,
                "read_at": "2026-01-01T00:00:00+00:00",
            }
        ),
    }
    await worker._process_event("r-1", read_fields)

    delivery_updates = [entry for entry in fake.stream_entries if entry[1].get("type") == "delivery.updated"]
    read_updates = [entry for entry in fake.stream_entries if entry[1].get("type") == "read.updated"]
    assert len(delivery_updates) == 2
    assert len(read_updates) == 2
