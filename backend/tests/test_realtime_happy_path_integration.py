import json

import pytest

from app.messaging.models import Conversation, ConversationMember, Message, OutboxEvent
from app.messaging.schemas import MessageCreateCommand
from app.messaging.service import acknowledge_delivered, acknowledge_read, send_message
from app.models.user import User
from app.realtime.protocol import ClientEventEnvelope
from app.workers.delivery_worker import DeliveryWorker
from app.workers.outbox_relay import OutboxRelayWorker
from app.realtime.presence_service import presence_service
from conftest import TestingSessionLocal


class FakeRedis:
    def __init__(self):
        self.set_data: dict[str, set[str]] = {}
        self.stream_data: dict[str, list[tuple[str, dict[str, str]]]] = {}
        self._stream_offsets: dict[str, int] = {}
        self.acked: list[tuple[str, str, str]] = []
        self.kv: dict[str, str] = {}
        self._id = 0

    async def xadd(self, stream: str, payload: dict[str, str], **kwargs):
        self._id += 1
        event_id = f"{self._id}-0"
        self.stream_data.setdefault(stream, []).append((event_id, payload))
        return event_id

    async def xgroup_create(self, name: str, groupname: str, id: str, mkstream: bool = True):
        self.stream_data.setdefault(name, [])
        return True

    async def xautoclaim(self, **kwargs):
        return ("0-0", [], [])

    async def xreadgroup(self, *, streams: dict[str, str], count: int = 100, **kwargs):
        entries = []
        for stream, marker in streams.items():
            data = self.stream_data.get(stream, [])
            if marker != ">":
                continue
            offset = self._stream_offsets.get(stream, 0)
            batch = data[offset : offset + count]
            if batch:
                self._stream_offsets[stream] = offset + len(batch)
                entries.append((stream, batch))
        return entries

    async def xack(self, stream: str, group: str, event_id: str):
        self.acked.append((stream, group, event_id))
        return 1

    async def exists(self, key: str):
        return int(key in self.kv or key in self.stream_data or key in self.set_data)

    async def setex(self, key: str, ttl: int, value: str):
        self.kv[key] = value
        return True

    async def scard(self, key: str):
        return len(self.set_data.get(key, set()))


def _seed_users_and_conversation():
    with TestingSessionLocal() as db:
        sender = User(id=1, email="sender@hp.dev", full_name="Sender", password_hash="x", is_active=True)
        recipient = User(id=2, email="recipient@hp.dev", full_name="Recipient", password_hash="x", is_active=True)
        db.add_all([sender, recipient])
        db.add(Conversation(id=501, kind="direct", created_by_user_id=1))
        db.add_all(
            [
                ConversationMember(conversation_id=501, user_id=1, role="owner"),
                ConversationMember(conversation_id=501, user_id=2, role="member"),
            ]
        )
        db.commit()


@pytest.mark.asyncio
async def test_realtime_main_happy_path_integration(monkeypatch):
    """
    Integration-style main flow:
      1) session.hello envelope parsing succeeds
      2) sender sends message -> durable message + outbox row
      3) outbox relay publishes message.created to delivery stream
      4) delivery worker processes stream and writes message.new to recipient realtime stream
      5) recipient delivered/read acks are persisted
    """
    _seed_users_and_conversation()

    # 1) session.hello parse success (transport/auth handshake mocked out in this integration test)
    parsed = ClientEventEnvelope.model_validate_json(
        json.dumps(
            {
                "v": 1,
                "event_id": "evt-happy-1",
                "type": "session.hello",
                "ts_ms": 1710000000000,
                "payload": {"protocol_version": 1, "resume": False, "last_server_seq_by_conversation": {"501": 0}},
            }
        )
    )
    assert parsed.type == "session.hello"

    # 2) Durable message acceptance.
    with TestingSessionLocal() as db:
        accepted = send_message(
            db,
            command=MessageCreateCommand(
                sender_user_id=1,
                conversation_id=501,
                client_msg_id="happy-path-msg-1",
                content_type="text",
                content={"text": "hello recipient"},
            ),
        )
        assert accepted.deduped is False
        assert accepted.outbox_event_id is not None

    with TestingSessionLocal() as db:
        assert db.query(Message).count() == 1
        outbox_rows = db.query(OutboxEvent).all()
        assert len(outbox_rows) == 1
        assert outbox_rows[0].event_type == "message.created"
        assert outbox_rows[0].status in {"pending", "published", "processing", "failed"}

    fake = FakeRedis()

    # 3) Outbox relay publishes to delivery stream.
    monkeypatch.setattr("app.workers.outbox_relay.SessionLocal", TestingSessionLocal)
    relay = OutboxRelayWorker()
    relay.redis = fake
    published_count = await relay.process_once()
    assert published_count == 1

    delivery_stream = f"{relay.settings.outbox_stream_prefix}:delivery"
    assert delivery_stream in fake.stream_data
    assert len(fake.stream_data[delivery_stream]) == 1

    # Mark recipient online for message.new fanout path.
    fake.set_data["sf:rt:v1:user:sockets:2"] = {"skt-online-2"}
    presence_service.redis = fake

    # 4) Delivery worker consumes delivery stream and fans out to recipient realtime stream.
    delivery_worker = DeliveryWorker()
    delivery_worker.redis = fake
    processed = await delivery_worker.process_once()
    assert processed >= 1

    realtime_stream = f"{delivery_worker.settings.outbox_stream_prefix}:realtime:2"
    assert realtime_stream in fake.stream_data
    assert len(fake.stream_data[realtime_stream]) == 1
    _, realtime_fields = fake.stream_data[realtime_stream][0]
    assert realtime_fields["type"] == "message.new"
    payload = json.loads(realtime_fields["payload_json"])
    assert int(payload["message_id"]) == accepted.message_id
    assert int(payload["conversation_id"]) == 501
    assert int(payload["server_seq"]) == accepted.server_seq

    # 5) Delivered/read paths where implemented.
    with TestingSessionLocal() as db:
        delivered = acknowledge_delivered(db, message_id=accepted.message_id, recipient_user_id=2)
        assert delivered.changed is True
        # second delivered ack idempotent
        delivered_again = acknowledge_delivered(db, message_id=accepted.message_id, recipient_user_id=2)
        assert delivered_again.changed is False

    with TestingSessionLocal() as db:
        read = acknowledge_read(
            db,
            conversation_id=501,
            recipient_user_id=2,
            read_upto_server_seq=accepted.server_seq,
        )
        assert read.changed is True
        # monotonic read cursor: same seq should not re-advance
        read_again = acknowledge_read(
            db,
            conversation_id=501,
            recipient_user_id=2,
            read_upto_server_seq=accepted.server_seq,
        )
        assert read_again.changed is False
