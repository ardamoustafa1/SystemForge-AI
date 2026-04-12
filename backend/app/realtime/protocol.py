from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


def now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def new_event_id() -> str:
    return str(uuid4())


class WsEnvelopeBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    v: Literal[1] = 1
    event_id: str = Field(default_factory=new_event_id, min_length=1, max_length=128)
    type: str = Field(min_length=1, max_length=64)
    ts_ms: int = Field(default_factory=now_ms, ge=0)
    trace_id: str | None = Field(default=None, min_length=1, max_length=128)
    correlation_id: str | None = Field(default=None, min_length=1, max_length=128)
    payload: dict[str, Any] = Field(default_factory=dict)


class SessionHelloPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    protocol_version: Literal[1] = 1
    resume: bool = False
    last_server_seq_by_conversation: dict[str, int] = Field(default_factory=dict)

    @field_validator("last_server_seq_by_conversation")
    @classmethod
    def _validate_last_seq(cls, value: dict[str, int]) -> dict[str, int]:
        for key, seq in value.items():
            int(key)
            if seq < 0:
                raise ValueError("sequence must be >= 0")
        return value


class SessionResumePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    last_server_seq_by_conversation: dict[str, int] = Field(default_factory=dict)

    @field_validator("last_server_seq_by_conversation")
    @classmethod
    def _validate_last_seq(cls, value: dict[str, int]) -> dict[str, int]:
        for key, seq in value.items():
            int(key)
            if seq < 0:
                raise ValueError("sequence must be >= 0")
        return value


class PresenceHeartbeatPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["online", "away"] = "online"
    client_ts_ms: int | None = Field(default=None, ge=0)


class MessageSendPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_msg_id: str = Field(min_length=1, max_length=64)
    conversation_id: int = Field(gt=0)
    content_type: Literal["text", "markdown", "json"] = "text"
    content: dict[str, Any] | str
    client_ts_ms: int | None = Field(default=None, ge=0)


class MessageDeliveredPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message_id: int = Field(gt=0)
    conversation_id: int | None = Field(default=None, gt=0)
    delivered_at_ms: int | None = Field(default=None, ge=0)


class MessageReadPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    conversation_id: int = Field(gt=0)
    read_upto_server_seq: int = Field(ge=0)
    read_at_ms: int | None = Field(default=None, ge=0)


class SyncRequestPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    conversation_id: int = Field(gt=0)
    after_server_seq: int = Field(default=0, ge=0)
    after_message_id: int | None = Field(default=None, gt=0)
    limit: int = Field(default=200, ge=1, le=1000)


class TypingPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    conversation_id: int = Field(gt=0)
    ttl_ms: int = Field(default=8000, ge=1000, le=30000)


class ClientEventEnvelope(WsEnvelopeBase):
    type: Literal[
        "session.hello",
        "session.resume",
        "presence.heartbeat",
        "message.send",
        "message.delivered",
        "message.read",
        "sync.request",
        "typing.started",
        "typing.stopped",
    ]


class ErrorPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=64)
    message: str = Field(min_length=1, max_length=512)
    retryable: bool = False
    retry_after_ms: int | None = Field(default=None, ge=0)


class SessionWelcomePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: int = Field(gt=0)
    socket_id: str = Field(min_length=1, max_length=128)
    server_ts_ms: int = Field(ge=0)
    heartbeat_interval_sec: int = Field(ge=5, le=120)
    session_expires_at_ms: int | None = Field(default=None, ge=0)


class SessionResumedPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: int = Field(gt=0)
    socket_id: str = Field(min_length=1, max_length=128)
    resumed: bool = True
    replayed_events: int = Field(default=0, ge=0)
    server_ts_ms: int = Field(ge=0)

