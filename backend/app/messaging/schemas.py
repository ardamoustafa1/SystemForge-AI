from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MessageCreateCommand:
    sender_user_id: int
    conversation_id: int
    client_msg_id: str
    content_type: str
    content: dict[str, Any] | str


@dataclass(frozen=True)
class MessageAcceptedResult:
    message_id: int
    conversation_id: int
    client_msg_id: str
    server_seq: int
    outbox_event_id: int | None
    deduped: bool


@dataclass(frozen=True)
class MessageDeliveredResult:
    message_id: int
    conversation_id: int
    recipient_user_id: int
    server_seq: int
    delivered_at_ms: int
    changed: bool
    outbox_event_id: int | None


@dataclass(frozen=True)
class MessageReadResult:
    conversation_id: int
    reader_user_id: int
    read_upto_server_seq: int
    read_message_id: int
    read_at_ms: int
    changed: bool
    outbox_event_id: int | None

