from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.messaging import repositories as repo
from app.messaging.schemas import (
    MessageAcceptedResult,
    MessageCreateCommand,
    MessageDeliveredResult,
    MessageReadResult,
)


class MessagingPermissionError(Exception):
    pass


class MessagingValidationError(Exception):
    pass


CLIENT_MSG_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,64}$")
ALLOWED_CONTENT_TYPES = {"text", "markdown", "json"}
MAX_TEXT_CHARS = 8000


def _normalize_content(content: dict[str, Any] | str) -> dict[str, Any]:
    if isinstance(content, str):
        return {"text": content}
    return content


def _validate_command(command: MessageCreateCommand) -> None:
    if command.conversation_id <= 0:
        raise MessagingValidationError("conversation_id must be positive")
    if command.sender_user_id <= 0:
        raise MessagingValidationError("sender_user_id must be positive")
    if command.content_type not in ALLOWED_CONTENT_TYPES:
        raise MessagingValidationError("Unsupported content_type")
    if not CLIENT_MSG_ID_RE.fullmatch(command.client_msg_id):
        raise MessagingValidationError("client_msg_id must match [A-Za-z0-9._:-]{1,64}")

    content_json = _normalize_content(command.content)
    if not content_json:
        raise MessagingValidationError("content must not be empty")
    if command.content_type == "text":
        text_value = content_json.get("text")
        if not isinstance(text_value, str) or not text_value.strip():
            raise MessagingValidationError("text content must include non-empty 'text'")
        if len(text_value) > MAX_TEXT_CHARS:
            raise MessagingValidationError(f"text content too long (max {MAX_TEXT_CHARS} chars)")


def _build_message_created_event_payload(
    *,
    message_id: int,
    conversation_id: int,
    sender_user_id: int,
    recipient_user_ids: list[int],
    content_type: str,
    content_json: dict[str, Any],
    server_seq: int,
    created_at: datetime,
) -> dict[str, Any]:
    return {
        "message_id": message_id,
        "conversation_id": conversation_id,
        "sender_user_id": sender_user_id,
        "recipient_user_ids": recipient_user_ids,
        "content_type": content_type,
        "content_json": content_json,
        "created_at": created_at.isoformat(),
        "server_seq": server_seq,
    }


def send_message(db: Session, *, command: MessageCreateCommand) -> MessageAcceptedResult:
    _validate_command(command)

    if not repo.is_active_conversation_member(
        db,
        conversation_id=command.conversation_id,
        user_id=command.sender_user_id,
    ):
        raise MessagingPermissionError("Sender is not an active member of this conversation")

    existing = repo.get_message_by_sender_client_id(
        db, sender_user_id=command.sender_user_id, client_msg_id=command.client_msg_id
    )
    if existing is not None:
        return MessageAcceptedResult(
            message_id=int(existing.id),
            conversation_id=int(existing.conversation_id),
            client_msg_id=existing.client_msg_id,
            server_seq=int(existing.server_seq),
            outbox_event_id=None,
            deduped=True,
        )

    content_json = _normalize_content(command.content)
    recipient_ids = repo.get_recipient_ids(
        db,
        conversation_id=command.conversation_id,
        sender_user_id=command.sender_user_id,
    )
    try:
        accepted_at = datetime.now(timezone.utc)
        server_seq = repo.allocate_server_seq(db, conversation_id=command.conversation_id)
        message = repo.create_message(
            db,
            sender_user_id=command.sender_user_id,
            conversation_id=command.conversation_id,
            client_msg_id=command.client_msg_id,
            content_type=command.content_type,
            content_json=content_json,
            server_seq=server_seq,
        )
        repo.create_message_recipients(
            db,
            message_id=int(message.id),
            conversation_id=command.conversation_id,
            recipient_user_ids=recipient_ids,
        )
        outbox = repo.create_outbox_event(
            db,
            aggregate_type="message",
            aggregate_id=int(message.id),
            event_type="message.created",
            # Message row + outbox row are inserted in the same DB transaction.
            payload_json=_build_message_created_event_payload(
                message_id=int(message.id),
                conversation_id=command.conversation_id,
                sender_user_id=command.sender_user_id,
                recipient_user_ids=recipient_ids,
                content_type=command.content_type,
                content_json=content_json,
                server_seq=server_seq,
                created_at=accepted_at,
            ),
        )
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise MessagingValidationError(str(exc)) from exc
    except IntegrityError:
        db.rollback()
        existing = repo.get_message_by_sender_client_id(
            db, sender_user_id=command.sender_user_id, client_msg_id=command.client_msg_id
        )
        if existing is None:
            raise
        return MessageAcceptedResult(
            message_id=int(existing.id),
            conversation_id=int(existing.conversation_id),
            client_msg_id=existing.client_msg_id,
            server_seq=int(existing.server_seq),
            outbox_event_id=None,
            deduped=True,
        )

    return MessageAcceptedResult(
        message_id=int(message.id),
        conversation_id=command.conversation_id,
        client_msg_id=command.client_msg_id,
        server_seq=server_seq,
        outbox_event_id=int(outbox.id),
        deduped=False,
    )


def acknowledge_delivered(
    db: Session,
    *,
    message_id: int,
    recipient_user_id: int,
) -> MessageDeliveredResult:
    if message_id <= 0:
        raise MessagingValidationError("message_id must be positive")
    if recipient_user_id <= 0:
        raise MessagingValidationError("recipient_user_id must be positive")

    state = repo.get_message_recipient_state(db, message_id=message_id, recipient_user_id=recipient_user_id)
    if state is None:
        raise MessagingPermissionError("Recipient is not authorized to acknowledge this message")
    conversation_id, server_seq, delivered_at = state

    changed = delivered_at is None
    event_id: int | None = None
    effective_delivered_at = delivered_at or datetime.now(timezone.utc)

    if changed:
        effective_delivered_at = datetime.now(timezone.utc)
        changed = repo.mark_delivered(
            db,
            message_id=message_id,
            recipient_user_id=recipient_user_id,
            delivered_at=effective_delivered_at,
        )
        if changed:
            outbox = repo.create_outbox_event(
                db,
                aggregate_type="message",
                aggregate_id=message_id,
                event_type="message.delivered",
                payload_json={
                    "message_id": message_id,
                    "conversation_id": conversation_id,
                    "recipient_user_id": recipient_user_id,
                    "server_seq": server_seq,
                    "delivered_at": effective_delivered_at.isoformat(),
                },
            )
            event_id = int(outbox.id)

    db.commit()
    return MessageDeliveredResult(
        message_id=message_id,
        conversation_id=conversation_id,
        recipient_user_id=recipient_user_id,
        server_seq=server_seq,
        delivered_at_ms=int(effective_delivered_at.timestamp() * 1000),
        changed=bool(changed),
        outbox_event_id=event_id,
    )


def acknowledge_read(
    db: Session,
    *,
    conversation_id: int,
    recipient_user_id: int,
    read_upto_server_seq: int,
) -> MessageReadResult:
    if conversation_id <= 0:
        raise MessagingValidationError("conversation_id must be positive")
    if recipient_user_id <= 0:
        raise MessagingValidationError("recipient_user_id must be positive")
    if read_upto_server_seq < 0:
        raise MessagingValidationError("read_upto_server_seq must be >= 0")

    member = repo.lock_active_member(db, conversation_id=conversation_id, user_id=recipient_user_id)
    if member is None:
        raise MessagingPermissionError("Reader is not an active conversation member")
    existing_last_read_message_id = int(member.last_read_message_id or 0)
    existing_last_read_at = member.last_read_at

    target_message = repo.get_message_by_conversation_and_seq_lte(
        db,
        conversation_id=conversation_id,
        server_seq=read_upto_server_seq,
    )
    if target_message is None:
        db.rollback()
        raise MessagingValidationError("No messages exist for the provided read_upto_server_seq")

    current_seq = -1
    current_message_id = member.last_read_message_id
    if current_message_id is not None:
        existing_seq = repo.get_message_seq(db, message_id=int(current_message_id))
        if existing_seq is not None:
            current_seq = existing_seq

    target_seq = int(target_message.server_seq)
    target_message_id = int(target_message.id)
    changed = target_seq > current_seq
    event_id: int | None = None
    read_at = datetime.now(timezone.utc)

    if changed:
        repo.update_member_read_cursor(
            db,
            conversation_id=conversation_id,
            user_id=recipient_user_id,
            read_message_id=target_message_id,
            read_at=read_at,
        )
        repo.mark_recipient_read_upto(
            db,
            conversation_id=conversation_id,
            recipient_user_id=recipient_user_id,
            read_upto_server_seq=target_seq,
            read_at=read_at,
        )
        outbox = repo.create_outbox_event(
            db,
            aggregate_type="conversation",
            aggregate_id=conversation_id,
            event_type="message.read",
            payload_json={
                "conversation_id": conversation_id,
                "reader_user_id": recipient_user_id,
                "read_upto_server_seq": target_seq,
                "read_message_id": target_message_id,
                "read_at": read_at.isoformat(),
            },
        )
        event_id = int(outbox.id)
        db.commit()
    else:
        db.rollback()
        if existing_last_read_at is not None:
            read_at = existing_last_read_at

    return MessageReadResult(
        conversation_id=conversation_id,
        reader_user_id=recipient_user_id,
        read_upto_server_seq=target_seq if changed else max(current_seq, 0),
        read_message_id=target_message_id if changed else (existing_last_read_message_id or target_message_id),
        read_at_ms=int(read_at.timestamp() * 1000),
        changed=changed,
        outbox_event_id=event_id,
    )


def build_sync_response(
    db: Session,
    *,
    requester_user_id: int,
    conversation_id: int,
    after_server_seq: int | None = None,
    after_message_id: int | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    if requester_user_id <= 0:
        raise MessagingValidationError("requester_user_id must be positive")
    if conversation_id <= 0:
        raise MessagingValidationError("conversation_id must be positive")
    safe_limit = max(1, min(limit, 500))
    if after_server_seq is not None and after_server_seq < 0:
        raise MessagingValidationError("after_server_seq must be >= 0")
    if after_message_id is not None and after_message_id <= 0:
        raise MessagingValidationError("after_message_id must be positive")

    if not repo.is_active_conversation_member(db, conversation_id=conversation_id, user_id=requester_user_id):
        raise MessagingPermissionError("Requester is not an active member of this conversation")

    try:
        if after_message_id is not None:
            messages = repo.list_messages_after_message_id(
                db,
                conversation_id=conversation_id,
                after_message_id=after_message_id,
                limit=safe_limit + 1,
            )
            resolved_after_server_seq = None
        else:
            anchor_seq = int(after_server_seq or 0)
            messages = repo.list_messages_after_server_seq(
                db,
                conversation_id=conversation_id,
                after_server_seq=anchor_seq,
                limit=safe_limit + 1,
            )
            resolved_after_server_seq = anchor_seq
    except ValueError as exc:
        raise MessagingValidationError(str(exc)) from exc

    has_more = len(messages) > safe_limit
    window = messages[:safe_limit]
    events: list[dict[str, Any]] = []
    for msg in window:
        events.append(
            {
                "type": "message.new",
                "payload": {
                    "message_id": int(msg.id),
                    "conversation_id": int(msg.conversation_id),
                    "sender_user_id": int(msg.sender_user_id),
                    "content_type": msg.content_type,
                    "content_json": msg.content_json,
                    "created_at": msg.created_at.isoformat() if msg.created_at else None,
                    "server_seq": int(msg.server_seq),
                    "client_msg_id": msg.client_msg_id,
                },
            }
        )

    last_server_seq = int(window[-1].server_seq) if window else int(after_server_seq or 0)
    return {
        "conversation_id": conversation_id,
        "after_server_seq": resolved_after_server_seq,
        "after_message_id": after_message_id,
        "events": events,
        "last_server_seq": last_server_seq,
        "has_more": has_more,
    }

