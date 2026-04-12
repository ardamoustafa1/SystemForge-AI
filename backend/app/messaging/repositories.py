from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import and_, or_, select, update
from sqlalchemy.orm import Session

from app.messaging.models import Conversation, ConversationMember, Message, MessageRecipient, OutboxEvent


def is_active_conversation_member(db: Session, *, conversation_id: int, user_id: int) -> bool:
    stmt = (
        select(ConversationMember.user_id)
        .where(
            and_(
                ConversationMember.conversation_id == conversation_id,
                ConversationMember.user_id == user_id,
                ConversationMember.left_at.is_(None),
            )
        )
        .limit(1)
    )
    return db.execute(stmt).scalar_one_or_none() is not None


def get_message_by_sender_client_id(
    db: Session, *, sender_user_id: int, client_msg_id: str
) -> Message | None:
    stmt = select(Message).where(
        and_(
            Message.sender_user_id == sender_user_id,
            Message.client_msg_id == client_msg_id,
        )
    )
    return db.execute(stmt).scalar_one_or_none()


def get_recipient_ids(db: Session, *, conversation_id: int, sender_user_id: int) -> list[int]:
    stmt = select(ConversationMember.user_id).where(
        and_(
            ConversationMember.conversation_id == conversation_id,
            ConversationMember.left_at.is_(None),
            ConversationMember.user_id != sender_user_id,
        )
    )
    return list(db.execute(stmt).scalars().all())


def list_active_member_ids(db: Session, *, conversation_id: int) -> list[int]:
    stmt = select(ConversationMember.user_id).where(
        and_(
            ConversationMember.conversation_id == conversation_id,
            ConversationMember.left_at.is_(None),
        )
    )
    return [int(user_id) for user_id in db.execute(stmt).scalars().all()]


def allocate_server_seq(db: Session, *, conversation_id: int) -> int:
    """
    Allocates a strictly monotonic per-conversation sequence under row lock.
    """
    lock_stmt = (
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .with_for_update()
    )
    conversation = db.execute(lock_stmt).scalar_one_or_none()
    if conversation is None:
        raise ValueError("Conversation not found")

    current = int(conversation.last_message_id or 0)
    next_seq = current + 1
    conversation.last_message_id = next_seq
    db.flush()
    return next_seq


def create_message(
    db: Session,
    *,
    sender_user_id: int,
    conversation_id: int,
    client_msg_id: str,
    content_type: str,
    content_json: dict[str, Any],
    server_seq: int,
) -> Message:
    message = Message(
        sender_user_id=sender_user_id,
        conversation_id=conversation_id,
        client_msg_id=client_msg_id,
        content_type=content_type,
        content_json=content_json,
        server_seq=server_seq,
    )
    db.add(message)
    db.flush()
    return message


def create_message_recipients(
    db: Session, *, message_id: int, conversation_id: int, recipient_user_ids: list[int]
) -> None:
    if not recipient_user_ids:
        return
    db.add_all(
        [
            MessageRecipient(
                message_id=message_id,
                conversation_id=conversation_id,
                recipient_user_id=recipient_user_id,
                delivery_status="pending",
            )
            for recipient_user_id in recipient_user_ids
        ]
    )


def create_outbox_event(
    db: Session,
    *,
    aggregate_type: str,
    aggregate_id: int,
    event_type: str,
    payload_json: dict[str, Any],
) -> OutboxEvent:
    event = OutboxEvent(
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        event_type=event_type,
        payload_json=payload_json,
        status="pending",
        attempts=0,
        next_attempt_at=datetime.now(timezone.utc),
    )
    db.add(event)
    db.flush()
    return event


def claim_outbox_events(
    db: Session,
    *,
    now: datetime,
    batch_size: int,
    processing_timeout_seconds: int,
) -> list[OutboxEvent]:
    stale_cutoff = now - timedelta(seconds=processing_timeout_seconds)
    stmt = (
        select(OutboxEvent)
        .where(
            or_(
                and_(
                    OutboxEvent.status.in_(["pending", "failed"]),
                    OutboxEvent.next_attempt_at <= now,
                ),
                and_(
                    OutboxEvent.status == "processing",
                    OutboxEvent.processing_started_at.is_not(None),
                    OutboxEvent.processing_started_at < stale_cutoff,
                ),
            )
        )
        .order_by(OutboxEvent.id.asc())
        .limit(batch_size)
        .with_for_update(skip_locked=True)
    )
    events = list(db.execute(stmt).scalars().all())
    for event in events:
        event.status = "processing"
        event.processing_started_at = now
        event.attempts = int(event.attempts or 0) + 1
    db.flush()
    return events


def mark_outbox_event_published(
    db: Session,
    *,
    outbox_event_id: int,
    published_at: datetime,
) -> bool:
    stmt = (
        update(OutboxEvent)
        .where(
            and_(
                OutboxEvent.id == outbox_event_id,
                OutboxEvent.status == "processing",
            )
        )
        .values(
            status="published",
            published_at=published_at,
            processing_started_at=None,
            last_error=None,
        )
    )
    result = db.execute(stmt)
    return bool(result.rowcount)


def mark_outbox_event_failed(
    db: Session,
    *,
    outbox_event_id: int,
    next_attempt_at: datetime,
    last_error: str,
) -> bool:
    stmt = (
        update(OutboxEvent)
        .where(
            and_(
                OutboxEvent.id == outbox_event_id,
                OutboxEvent.status == "processing",
            )
        )
        .values(
            status="failed",
            next_attempt_at=next_attempt_at,
            processing_started_at=None,
            last_error=last_error[:2000],
        )
    )
    result = db.execute(stmt)
    return bool(result.rowcount)


def mark_delivered(
    db: Session,
    *,
    message_id: int,
    recipient_user_id: int,
    delivered_at: datetime | None = None,
) -> bool:
    effective_delivered_at = delivered_at or datetime.now(timezone.utc)
    stmt = (
        update(MessageRecipient)
        .where(
            and_(
                MessageRecipient.message_id == message_id,
                MessageRecipient.recipient_user_id == recipient_user_id,
                MessageRecipient.delivered_at.is_(None),
            )
        )
        .values(delivered_at=effective_delivered_at, delivery_status="delivered")
    )
    result = db.execute(stmt)
    return result.rowcount > 0


def get_message_recipient_state(
    db: Session,
    *,
    message_id: int,
    recipient_user_id: int,
) -> tuple[int, int, datetime | None] | None:
    stmt = (
        select(MessageRecipient.conversation_id, Message.server_seq, MessageRecipient.delivered_at)
        .join(Message, Message.id == MessageRecipient.message_id)
        .where(
            and_(
                MessageRecipient.message_id == message_id,
                MessageRecipient.recipient_user_id == recipient_user_id,
            )
        )
        .limit(1)
    )
    row = db.execute(stmt).one_or_none()
    if row is None:
        return None
    return int(row[0]), int(row[1]), row[2]


def lock_active_member(
    db: Session,
    *,
    conversation_id: int,
    user_id: int,
) -> ConversationMember | None:
    stmt = (
        select(ConversationMember)
        .where(
            and_(
                ConversationMember.conversation_id == conversation_id,
                ConversationMember.user_id == user_id,
                ConversationMember.left_at.is_(None),
            )
        )
        .with_for_update()
        .limit(1)
    )
    return db.execute(stmt).scalar_one_or_none()


def get_message_by_conversation_and_seq_lte(
    db: Session,
    *,
    conversation_id: int,
    server_seq: int,
) -> Message | None:
    stmt = (
        select(Message)
        .where(
            and_(
                Message.conversation_id == conversation_id,
                Message.server_seq <= server_seq,
            )
        )
        .order_by(Message.server_seq.desc())
        .limit(1)
    )
    return db.execute(stmt).scalar_one_or_none()


def get_message_seq(
    db: Session,
    *,
    message_id: int,
) -> int | None:
    stmt = select(Message.server_seq).where(Message.id == message_id).limit(1)
    result = db.execute(stmt).scalar_one_or_none()
    return int(result) if result is not None else None


def list_messages_after_server_seq(
    db: Session,
    *,
    conversation_id: int,
    after_server_seq: int,
    limit: int,
) -> list[Message]:
    stmt = (
        select(Message)
        .where(
            and_(
                Message.conversation_id == conversation_id,
                Message.server_seq > after_server_seq,
            )
        )
        .order_by(Message.server_seq.asc())
        .limit(limit)
    )
    return list(db.execute(stmt).scalars().all())


def list_messages_after_message_id(
    db: Session,
    *,
    conversation_id: int,
    after_message_id: int,
    limit: int,
) -> list[Message]:
    anchor_stmt = (
        select(Message.server_seq)
        .where(
            and_(
                Message.id == after_message_id,
                Message.conversation_id == conversation_id,
            )
        )
        .limit(1)
    )
    anchor_seq = db.execute(anchor_stmt).scalar_one_or_none()
    if anchor_seq is None:
        raise ValueError("after_message_id does not belong to conversation")
    return list_messages_after_server_seq(
        db,
        conversation_id=conversation_id,
        after_server_seq=int(anchor_seq),
        limit=limit,
    )


def update_member_read_cursor(
    db: Session,
    *,
    conversation_id: int,
    user_id: int,
    read_message_id: int,
    read_at: datetime,
) -> None:
    stmt = (
        update(ConversationMember)
        .where(
            and_(
                ConversationMember.conversation_id == conversation_id,
                ConversationMember.user_id == user_id,
            )
        )
        .values(
            last_read_message_id=read_message_id,
            last_read_at=read_at,
        )
    )
    db.execute(stmt)


def mark_recipient_read_upto(
    db: Session,
    *,
    conversation_id: int,
    recipient_user_id: int,
    read_upto_server_seq: int,
    read_at: datetime,
) -> int:
    message_ids_subquery = select(Message.id).where(
        and_(
            Message.conversation_id == conversation_id,
            Message.server_seq <= read_upto_server_seq,
        )
    )
    stmt = (
        update(MessageRecipient)
        .where(
            and_(
                MessageRecipient.recipient_user_id == recipient_user_id,
                MessageRecipient.conversation_id == conversation_id,
                MessageRecipient.read_at.is_(None),
                MessageRecipient.message_id.in_(message_ids_subquery),
            )
        )
        .values(read_at=read_at)
    )
    result = db.execute(stmt)
    return int(result.rowcount or 0)

