import json

import pytest
from pydantic import ValidationError

from app.messaging.models import Conversation, ConversationMember, Message, MessageRecipient, OutboxEvent
from app.messaging.schemas import MessageCreateCommand
from app.messaging.service import (
    MessagingPermissionError,
    MessagingValidationError,
    acknowledge_delivered,
    acknowledge_read,
    build_sync_response,
    send_message,
)
from app.models.user import User
from app.realtime.protocol import ClientEventEnvelope
from app.realtime.protocol import SyncRequestPayload
from conftest import TestingSessionLocal


def _seed_users_and_conversation() -> tuple[int, int, int]:
    with TestingSessionLocal() as db:
        sender = User(id=1, email="sender@test.dev", full_name="Sender", password_hash="x", is_active=True)
        recipient = User(id=2, email="recipient@test.dev", full_name="Recipient", password_hash="x", is_active=True)
        outsider = User(id=3, email="outsider@test.dev", full_name="Outsider", password_hash="x", is_active=True)
        db.add_all([sender, recipient, outsider])
        db.add(Conversation(id=100, kind="direct", created_by_user_id=1))
        db.add_all(
            [
                ConversationMember(conversation_id=100, user_id=1, role="owner"),
                ConversationMember(conversation_id=100, user_id=2, role="member"),
            ]
        )
        db.commit()
    return 1, 2, 3


def test_session_hello_parsing():
    envelope = ClientEventEnvelope.model_validate_json(
        json.dumps(
            {
                "v": 1,
                "event_id": "evt-1",
                "type": "session.hello",
                "ts_ms": 1710000000000,
                "payload": {"protocol_version": 1, "resume": False, "last_server_seq_by_conversation": {"100": 7}},
            }
        )
    )
    assert envelope.type == "session.hello"
    assert envelope.payload["protocol_version"] == 1


def test_invalid_envelope_rejection():
    with pytest.raises(ValidationError):
        ClientEventEnvelope.model_validate_json(
            json.dumps(
                {
                    "v": 1,
                    "event_id": "evt-2",
                    "type": "session.hello",
                    "ts_ms": 1710000000000,
                    "payload": {},
                    "unknown_field": "not-allowed",
                }
            )
        )


def test_sync_request_requires_conversation_id():
    with pytest.raises(ValidationError):
        SyncRequestPayload.model_validate({"after_server_seq": 0, "limit": 20})


def test_message_send_idempotency_and_outbox_creation():
    sender_id, _, _ = _seed_users_and_conversation()
    command = MessageCreateCommand(
        sender_user_id=sender_id,
        conversation_id=100,
        client_msg_id="msg-001",
        content_type="text",
        content={"text": "hello"},
    )

    with TestingSessionLocal() as db:
        first = send_message(db, command=command)
    with TestingSessionLocal() as db:
        second = send_message(db, command=command)

    assert first.deduped is False
    assert second.deduped is True
    assert first.message_id == second.message_id

    with TestingSessionLocal() as db:
        assert db.query(Message).count() == 1
        assert db.query(MessageRecipient).count() == 1
        outbox = db.query(OutboxEvent).all()
        assert len(outbox) == 1
        assert outbox[0].event_type == "message.created"
        assert int(outbox[0].aggregate_id) == first.message_id


def test_message_send_durable_creation_persists_payload_and_recipient():
    sender_id, recipient_id, _ = _seed_users_and_conversation()
    with TestingSessionLocal() as db:
        accepted = send_message(
            db,
            command=MessageCreateCommand(
                sender_user_id=sender_id,
                conversation_id=100,
                client_msg_id="msg-durable-1",
                content_type="text",
                content={"text": "durable payload"},
            ),
        )
        assert accepted.deduped is False
        assert accepted.outbox_event_id is not None

    with TestingSessionLocal() as db:
        message = db.query(Message).filter(Message.id == accepted.message_id).one()
        assert int(message.conversation_id) == 100
        assert message.content_json["text"] == "durable payload"
        recipients = db.query(MessageRecipient).filter(MessageRecipient.message_id == accepted.message_id).all()
        assert len(recipients) == 1
        assert int(recipients[0].recipient_user_id) == recipient_id


def test_conversation_membership_enforced_for_send():
    _seed_users_and_conversation()
    with TestingSessionLocal() as db:
        with pytest.raises(MessagingPermissionError):
            send_message(
                db,
                command=MessageCreateCommand(
                    sender_user_id=3,
                    conversation_id=100,
                    client_msg_id="msg-outsider",
                    content_type="text",
                    content={"text": "not allowed"},
                ),
            )


def test_delivered_ack_requires_valid_recipient():
    sender_id, recipient_id, outsider_id = _seed_users_and_conversation()
    with TestingSessionLocal() as db:
        accepted = send_message(
            db,
            command=MessageCreateCommand(
                sender_user_id=sender_id,
                conversation_id=100,
                client_msg_id="msg-delivered",
                content_type="text",
                content={"text": "ack me"},
            ),
        )
    with TestingSessionLocal() as db:
        ok = acknowledge_delivered(db, message_id=accepted.message_id, recipient_user_id=recipient_id)
        assert ok.changed is True
        assert ok.outbox_event_id is not None
    with TestingSessionLocal() as db:
        second = acknowledge_delivered(db, message_id=accepted.message_id, recipient_user_id=recipient_id)
        assert second.changed is False
        assert second.outbox_event_id is None
    with TestingSessionLocal() as db:
        with pytest.raises(MessagingPermissionError):
            acknowledge_delivered(db, message_id=accepted.message_id, recipient_user_id=outsider_id)


def test_read_cursor_monotonic_behavior():
    sender_id, recipient_id, _ = _seed_users_and_conversation()
    with TestingSessionLocal() as db:
        m1 = send_message(
            db,
            command=MessageCreateCommand(
                sender_user_id=sender_id,
                conversation_id=100,
                client_msg_id="msg-r1",
                content_type="text",
                content={"text": "m1"},
            ),
        )
        m2 = send_message(
            db,
            command=MessageCreateCommand(
                sender_user_id=sender_id,
                conversation_id=100,
                client_msg_id="msg-r2",
                content_type="text",
                content={"text": "m2"},
            ),
        )

    with TestingSessionLocal() as db:
        advanced = acknowledge_read(
            db,
            conversation_id=100,
            recipient_user_id=recipient_id,
            read_upto_server_seq=m2.server_seq,
        )
        assert advanced.changed is True
        assert advanced.read_upto_server_seq == m2.server_seq

    with TestingSessionLocal() as db:
        stale = acknowledge_read(
            db,
            conversation_id=100,
            recipient_user_id=recipient_id,
            read_upto_server_seq=m1.server_seq,
        )
        assert stale.changed is False
        assert stale.read_upto_server_seq >= m2.server_seq


def test_read_cursor_requires_membership():
    sender_id, _, outsider_id = _seed_users_and_conversation()
    with TestingSessionLocal() as db:
        m1 = send_message(
            db,
            command=MessageCreateCommand(
                sender_user_id=sender_id,
                conversation_id=100,
                client_msg_id="msg-r-membership",
                content_type="text",
                content={"text": "m1"},
            ),
        )
        assert m1.server_seq > 0
    with TestingSessionLocal() as db:
        with pytest.raises(MessagingPermissionError):
            acknowledge_read(
                db,
                conversation_id=100,
                recipient_user_id=outsider_id,
                read_upto_server_seq=1,
            )


def test_sync_request_response_after_seq():
    sender_id, recipient_id, _ = _seed_users_and_conversation()
    with TestingSessionLocal() as db:
        first = send_message(
            db,
            command=MessageCreateCommand(
                sender_user_id=sender_id,
                conversation_id=100,
                client_msg_id="msg-sync-1",
                content_type="text",
                content={"text": "first"},
            ),
        )
        second = send_message(
            db,
            command=MessageCreateCommand(
                sender_user_id=sender_id,
                conversation_id=100,
                client_msg_id="msg-sync-2",
                content_type="text",
                content={"text": "second"},
            ),
        )
        assert second.server_seq > first.server_seq

    with TestingSessionLocal() as db:
        replay = build_sync_response(
            db,
            requester_user_id=recipient_id,
            conversation_id=100,
            after_server_seq=first.server_seq,
            limit=50,
        )
    assert replay["conversation_id"] == 100
    assert replay["after_server_seq"] == first.server_seq
    assert replay["has_more"] is False
    assert len(replay["events"]) == 1
    assert replay["events"][0]["type"] == "message.new"
    assert replay["events"][0]["payload"]["server_seq"] == second.server_seq


def test_sync_request_response_after_message_id_and_membership():
    sender_id, recipient_id, outsider_id = _seed_users_and_conversation()
    with TestingSessionLocal() as db:
        first = send_message(
            db,
            command=MessageCreateCommand(
                sender_user_id=sender_id,
                conversation_id=100,
                client_msg_id="msg-sync-mid-1",
                content_type="text",
                content={"text": "first"},
            ),
        )
        second = send_message(
            db,
            command=MessageCreateCommand(
                sender_user_id=sender_id,
                conversation_id=100,
                client_msg_id="msg-sync-mid-2",
                content_type="text",
                content={"text": "second"},
            ),
        )
        assert second.server_seq > first.server_seq

    with TestingSessionLocal() as db:
        replay = build_sync_response(
            db,
            requester_user_id=recipient_id,
            conversation_id=100,
            after_message_id=first.message_id,
            limit=50,
        )
    assert replay["after_message_id"] == first.message_id
    assert replay["events"][0]["payload"]["message_id"] == second.message_id

    with TestingSessionLocal() as db:
        with pytest.raises(MessagingPermissionError):
            build_sync_response(
                db,
                requester_user_id=outsider_id,
                conversation_id=100,
                after_message_id=first.message_id,
                limit=50,
            )


def test_sync_request_rejects_invalid_after_message_id():
    sender_id, recipient_id, _ = _seed_users_and_conversation()
    with TestingSessionLocal() as db:
        send_message(
            db,
            command=MessageCreateCommand(
                sender_user_id=sender_id,
                conversation_id=100,
                client_msg_id="msg-sync-invalid-anchor",
                content_type="text",
                content={"text": "hello"},
            ),
        )

    with TestingSessionLocal() as db:
        with pytest.raises(MessagingValidationError):
            build_sync_response(
                db,
                requester_user_id=recipient_id,
                conversation_id=100,
                after_message_id=999999,
                limit=20,
            )
