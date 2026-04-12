from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from jose import JWTError, jwt
from pydantic import ValidationError

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.messaging.schemas import MessageCreateCommand
from app.messaging.service import (
    MessagingPermissionError,
    MessagingValidationError,
    acknowledge_read,
    acknowledge_delivered,
    build_sync_response,
    send_message,
)
from app.models import User
from app.realtime.connection_manager import connection_manager
from app.realtime.presence_service import presence_service
from app.realtime.protocol import (
    ClientEventEnvelope,
    ErrorPayload,
    MessageDeliveredPayload,
    MessageReadPayload,
    MessageSendPayload,
    PresenceHeartbeatPayload,
    SessionHelloPayload,
    SessionResumePayload,
    SessionResumedPayload,
    SessionWelcomePayload,
    SyncRequestPayload,
    TypingPayload,
)

logger = logging.getLogger("systemforge.realtime")
router = APIRouter(tags=["realtime"])


def _now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def _build_event(
    *,
    event_type: str,
    payload: dict[str, Any],
    trace_id: str | None,
    correlation_event_id: str | None = None,
) -> dict[str, Any]:
    return {
        "v": 1,
        "event_id": str(uuid4()),
        "type": event_type,
        "ts_ms": _now_ms(),
        "trace_id": trace_id or str(uuid4()),
        "correlation_id": correlation_event_id,
        "payload": payload,
    }


async def _send_error(
    *,
    websocket: WebSocket,
    code: str,
    message: str,
    retryable: bool,
    trace_id: str | None,
    correlation_event_id: str | None = None,
    retry_after_ms: int | None = None,
) -> None:
    payload = ErrorPayload(
        code=code,
        message=message,
        retryable=retryable,
        retry_after_ms=retry_after_ms,
    ).model_dump(mode="json", exclude_none=True)
    await websocket.send_json(
        _build_event(
            event_type="error",
            payload=payload,
            trace_id=trace_id,
            correlation_event_id=correlation_event_id,
        )
    )


def _extract_bearer_token(websocket: WebSocket) -> str | None:
    auth_header = websocket.headers.get("authorization")
    if not auth_header:
        return None
    if not auth_header.lower().startswith("bearer "):
        return None
    return auth_header.split(" ", 1)[1].strip() or None


def _authenticate_websocket(websocket: WebSocket) -> User | None:
    settings = get_settings()
    token = websocket.cookies.get(settings.auth_cookie_name) or _extract_bearer_token(websocket)
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = int(payload.get("sub", "0"))
    except (JWTError, ValueError):
        return None
    if user_id <= 0:
        return None
    with SessionLocal() as db:
        user = db.get(User, user_id)
        if not user or not user.is_active:
            return None
        db.expunge(user)
        return user


@router.websocket("/ws")
async def websocket_gateway(websocket: WebSocket) -> None:
    user = _authenticate_websocket(websocket)
    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication required")
        return

    socket_id = f"skt_{uuid4().hex}"
    await websocket.accept()
    await connection_manager.connect(user_id=user.id, socket_id=socket_id, websocket=websocket)
    try:
        await presence_service.register_session(user_id=user.id, socket_id=socket_id)
    except Exception:
        logger.exception("ws_presence_connect_failed", extra={"user_id": user.id, "socket_id": socket_id})

    welcome_payload = SessionWelcomePayload(
        user_id=user.id,
        socket_id=socket_id,
        server_ts_ms=_now_ms(),
        heartbeat_interval_sec=presence_service.recommended_heartbeat_interval_seconds(),
    )
    session_hello_received = False

    settings = get_settings()
    user_stream = f"{settings.outbox_stream_prefix}:realtime:{user.id}"
    ws_group = f"ws-{socket_id}"

    async def _stream_forwarder() -> None:
        redis = presence_service.redis
        try:
            await redis.xgroup_create(name=user_stream, groupname=ws_group, id="$", mkstream=True)
        except Exception as exc:
            if "BUSYGROUP" not in str(exc):
                raise
        while True:
            entries = await redis.xreadgroup(
                groupname=ws_group,
                consumername=socket_id,
                streams={user_stream: ">"},
                count=100,
                block=2000,
            )
            if not entries:
                continue
            for _, stream_entries in entries:
                for entry_id, fields in stream_entries:
                    evt_type = fields.get("type", "message.new")
                    payload_json = fields.get("payload_json", "{}")
                    try:
                        payload = json.loads(payload_json)
                    except Exception:
                        payload = {}
                    await websocket.send_json(
                        _build_event(
                            event_type=evt_type,
                            payload=payload,
                            trace_id=None,
                            correlation_event_id=None,
                        )
                    )
                    await redis.xack(user_stream, ws_group, entry_id)

    forwarder_task = asyncio.create_task(_stream_forwarder())

    logger.info("ws_connected", extra={"user_id": user.id, "socket_id": socket_id})
    try:
        while True:
            raw = await websocket.receive_text()
            if len(raw) > 32_768:
                await _send_error(
                    websocket=websocket,
                    code="PAYLOAD_TOO_LARGE",
                    message="WebSocket payload too large",
                    retryable=False,
                    trace_id=None,
                )
                continue

            try:
                envelope_data = json.loads(raw)
            except json.JSONDecodeError:
                await _send_error(
                    websocket=websocket,
                    code="INVALID_JSON",
                    message="Invalid JSON payload",
                    retryable=False,
                    trace_id=None,
                )
                continue

            try:
                envelope = ClientEventEnvelope.model_validate(envelope_data)
            except ValidationError:
                await _send_error(
                    websocket=websocket,
                    code="INVALID_ENVELOPE",
                    message="Invalid event envelope",
                    retryable=False,
                    trace_id=None,
                )
                continue

            event_type = envelope.type
            if event_type == "session.hello":
                try:
                    SessionHelloPayload.model_validate(envelope.payload)
                except ValidationError as exc:
                    await _send_error(
                        websocket=websocket,
                        code="INVALID_SESSION_HELLO",
                        message=exc.errors()[0]["msg"],
                        retryable=False,
                        trace_id=envelope.trace_id,
                        correlation_event_id=envelope.event_id,
                    )
                    continue
                await websocket.send_json(
                    _build_event(
                        event_type="session.welcome",
                        payload=welcome_payload.model_dump(mode="json", exclude_none=True),
                        trace_id=envelope.trace_id,
                        correlation_event_id=envelope.event_id,
                    )
                )
                session_hello_received = True
                continue

            if not session_hello_received:
                await _send_error(
                    websocket=websocket,
                    code="SESSION_NOT_INITIALIZED",
                    message="Send session.hello before other events",
                    retryable=False,
                    trace_id=envelope.trace_id,
                    correlation_event_id=envelope.event_id,
                )
                continue

            if event_type == "presence.heartbeat":
                try:
                    heartbeat_payload = PresenceHeartbeatPayload.model_validate(envelope.payload)
                    await presence_service.heartbeat(
                        user_id=user.id,
                        socket_id=socket_id,
                        status=heartbeat_payload.status,
                    )
                except Exception:
                    logger.exception("ws_presence_heartbeat_failed", extra={"user_id": user.id, "socket_id": socket_id})
                await websocket.send_json(
                    _build_event(
                        event_type="pong",
                        payload={"socket_id": socket_id, "server_ts_ms": _now_ms()},
                        trace_id=envelope.trace_id,
                        correlation_event_id=envelope.event_id,
                    )
                )
                continue

            if event_type == "session.resume":
                try:
                    resume_payload = SessionResumePayload.model_validate(envelope.payload)
                except ValidationError as exc:
                    await _send_error(
                        websocket=websocket,
                        code="INVALID_SESSION_RESUME",
                        message=exc.errors()[0]["msg"],
                        retryable=False,
                        trace_id=envelope.trace_id,
                        correlation_event_id=envelope.event_id,
                    )
                    continue

                replayed_events = 0
                requires_sync = False
                # Bounded server-side replay by conversation anchors from the client.
                # This avoids immediate sync round-trips on reconnect while keeping
                # replay scope explicit and predictable.
                if resume_payload.last_server_seq_by_conversation:
                    with SessionLocal() as db:
                        for raw_conversation_id, last_seq in list(resume_payload.last_server_seq_by_conversation.items())[:50]:
                            try:
                                conversation_id = int(raw_conversation_id)
                                sync_result = build_sync_response(
                                    db,
                                    requester_user_id=user.id,
                                    conversation_id=conversation_id,
                                    after_server_seq=int(last_seq),
                                    limit=200,
                                )
                            except (ValueError, MessagingPermissionError, MessagingValidationError):
                                continue
                            events = sync_result.get("events", [])
                            for replay_event in events:
                                evt_type = str(replay_event.get("type", "message.new"))
                                evt_payload = replay_event.get("payload", {})
                                await websocket.send_json(
                                    _build_event(
                                        event_type=evt_type,
                                        payload=evt_payload if isinstance(evt_payload, dict) else {},
                                        trace_id=envelope.trace_id,
                                        correlation_event_id=envelope.event_id,
                                    )
                                )
                            replayed_events += len(events)
                            if bool(sync_result.get("has_more")):
                                requires_sync = True

                resumed_payload = SessionResumedPayload(
                    user_id=user.id,
                    socket_id=socket_id,
                    resumed=True,
                    replayed_events=replayed_events,
                    server_ts_ms=_now_ms(),
                )
                response_payload = resumed_payload.model_dump(mode="json", exclude_none=True)
                if requires_sync:
                    response_payload["requires_sync"] = True
                await websocket.send_json(
                    _build_event(
                        event_type="session.resumed",
                        payload=response_payload,
                        trace_id=envelope.trace_id,
                        correlation_event_id=envelope.event_id,
                    )
                )
                continue

            if event_type == "message.send":
                try:
                    message_payload = MessageSendPayload.model_validate(envelope.payload)
                except ValidationError as exc:
                    await _send_error(
                        websocket=websocket,
                        code="INVALID_MESSAGE_SEND",
                        message=exc.errors()[0]["msg"],
                        retryable=False,
                        trace_id=envelope.trace_id,
                        correlation_event_id=envelope.event_id,
                    )
                    continue

                try:
                    with SessionLocal() as db:
                        result = send_message(
                            db,
                            command=MessageCreateCommand(
                                sender_user_id=user.id,
                                conversation_id=message_payload.conversation_id,
                                client_msg_id=message_payload.client_msg_id,
                                content_type=message_payload.content_type,
                                content=message_payload.content,
                            ),
                        )
                except MessagingPermissionError as exc:
                    await _send_error(
                        websocket=websocket,
                        code="NOT_MEMBER",
                        message=str(exc),
                        retryable=False,
                        trace_id=envelope.trace_id,
                        correlation_event_id=envelope.event_id,
                    )
                    continue
                except MessagingValidationError as exc:
                    await _send_error(
                        websocket=websocket,
                        code="INVALID_MESSAGE_SEND",
                        message=str(exc),
                        retryable=False,
                        trace_id=envelope.trace_id,
                        correlation_event_id=envelope.event_id,
                    )
                    continue
                except Exception:
                    logger.exception("ws_message_send_failed", extra={"user_id": user.id, "socket_id": socket_id})
                    await _send_error(
                        websocket=websocket,
                        code="SEND_FAILED",
                        message="Failed to persist message",
                        retryable=True,
                        retry_after_ms=500,
                        trace_id=envelope.trace_id,
                        correlation_event_id=envelope.event_id,
                    )
                    continue

                await websocket.send_json(
                    _build_event(
                        event_type="message.accepted",
                        payload={
                            "message_id": result.message_id,
                            "client_msg_id": result.client_msg_id,
                            "conversation_id": result.conversation_id,
                            "server_seq": result.server_seq,
                            "outbox_event_id": result.outbox_event_id,
                            "deduped": result.deduped,
                            "accepted_at_ms": _now_ms(),
                        },
                        trace_id=envelope.trace_id,
                        correlation_event_id=envelope.event_id,
                    )
                )
                continue

            if event_type == "message.delivered":
                try:
                    delivered = MessageDeliveredPayload.model_validate(envelope.payload)
                    with SessionLocal() as db:
                        delivered_result = acknowledge_delivered(
                            db,
                            message_id=delivered.message_id,
                            recipient_user_id=user.id,
                        )
                except ValidationError as exc:
                    await _send_error(
                        websocket=websocket,
                        code="INVALID_DELIVERED_ACK",
                        message=exc.errors()[0]["msg"],
                        retryable=False,
                        trace_id=envelope.trace_id,
                        correlation_event_id=envelope.event_id,
                    )
                    continue
                except MessagingPermissionError as exc:
                    await _send_error(
                        websocket=websocket,
                        code="NOT_RECIPIENT",
                        message=str(exc),
                        retryable=False,
                        trace_id=envelope.trace_id,
                        correlation_event_id=envelope.event_id,
                    )
                    continue
                except MessagingValidationError as exc:
                    await _send_error(
                        websocket=websocket,
                        code="INVALID_DELIVERED_ACK",
                        message=str(exc),
                        retryable=False,
                        trace_id=envelope.trace_id,
                        correlation_event_id=envelope.event_id,
                    )
                    continue
                except Exception:
                    logger.exception("ws_message_delivered_failed", extra={"user_id": user.id, "socket_id": socket_id})
                    await _send_error(
                        websocket=websocket,
                        code="DELIVERED_ACK_FAILED",
                        message="Failed to process delivered acknowledgment",
                        retryable=True,
                        retry_after_ms=500,
                        trace_id=envelope.trace_id,
                        correlation_event_id=envelope.event_id,
                    )
                    continue

                await websocket.send_json(
                    _build_event(
                        event_type="ack",
                        payload={
                            "received_type": event_type,
                            "message_id": delivered_result.message_id,
                            "conversation_id": delivered_result.conversation_id,
                            "recipient_user_id": delivered_result.recipient_user_id,
                            "server_seq": delivered_result.server_seq,
                            "delivered_at_ms": delivered_result.delivered_at_ms,
                            "changed": delivered_result.changed,
                            "outbox_event_id": delivered_result.outbox_event_id,
                            "received_at_ms": _now_ms(),
                        },
                        trace_id=envelope.trace_id,
                        correlation_event_id=envelope.event_id,
                    )
                )
                continue

            if event_type == "message.read":
                try:
                    read_payload = MessageReadPayload.model_validate(envelope.payload)
                    with SessionLocal() as db:
                        read_result = acknowledge_read(
                            db,
                            conversation_id=read_payload.conversation_id,
                            recipient_user_id=user.id,
                            read_upto_server_seq=read_payload.read_upto_server_seq,
                        )
                except ValidationError as exc:
                    await _send_error(
                        websocket=websocket,
                        code="INVALID_READ_ACK",
                        message=exc.errors()[0]["msg"],
                        retryable=False,
                        trace_id=envelope.trace_id,
                        correlation_event_id=envelope.event_id,
                    )
                    continue
                except MessagingPermissionError as exc:
                    await _send_error(
                        websocket=websocket,
                        code="NOT_MEMBER",
                        message=str(exc),
                        retryable=False,
                        trace_id=envelope.trace_id,
                        correlation_event_id=envelope.event_id,
                    )
                    continue
                except MessagingValidationError as exc:
                    await _send_error(
                        websocket=websocket,
                        code="INVALID_READ_ACK",
                        message=str(exc),
                        retryable=False,
                        trace_id=envelope.trace_id,
                        correlation_event_id=envelope.event_id,
                    )
                    continue
                await websocket.send_json(
                    _build_event(
                        event_type="ack",
                        payload={
                            "received_type": event_type,
                            "conversation_id": read_result.conversation_id,
                            "reader_user_id": read_result.reader_user_id,
                            "read_upto_server_seq": read_result.read_upto_server_seq,
                            "read_message_id": read_result.read_message_id,
                            "read_at_ms": read_result.read_at_ms,
                            "changed": read_result.changed,
                            "outbox_event_id": read_result.outbox_event_id,
                            "received_at_ms": _now_ms(),
                        },
                        trace_id=envelope.trace_id,
                        correlation_event_id=envelope.event_id,
                    )
                )
                continue

            if event_type == "sync.request":
                try:
                    sync_payload = SyncRequestPayload.model_validate(envelope.payload)
                    with SessionLocal() as db:
                        sync_result = build_sync_response(
                            db,
                            requester_user_id=user.id,
                            conversation_id=sync_payload.conversation_id,
                            after_server_seq=sync_payload.after_server_seq,
                            after_message_id=sync_payload.after_message_id,
                            limit=sync_payload.limit,
                        )
                except ValidationError as exc:
                    await _send_error(
                        websocket=websocket,
                        code="INVALID_SYNC_REQUEST",
                        message=exc.errors()[0]["msg"],
                        retryable=False,
                        trace_id=envelope.trace_id,
                        correlation_event_id=envelope.event_id,
                    )
                    continue
                except MessagingPermissionError as exc:
                    await _send_error(
                        websocket=websocket,
                        code="NOT_MEMBER",
                        message=str(exc),
                        retryable=False,
                        trace_id=envelope.trace_id,
                        correlation_event_id=envelope.event_id,
                    )
                    continue
                except MessagingValidationError as exc:
                    await _send_error(
                        websocket=websocket,
                        code="INVALID_SYNC_REQUEST",
                        message=str(exc),
                        retryable=False,
                        trace_id=envelope.trace_id,
                        correlation_event_id=envelope.event_id,
                    )
                    continue
                await websocket.send_json(
                    _build_event(
                        event_type="sync.response",
                        payload={
                            "conversation_id": sync_result["conversation_id"],
                            "after_server_seq": sync_result["after_server_seq"],
                            "after_message_id": sync_result["after_message_id"],
                            "events": sync_result["events"],
                            "last_server_seq": sync_result["last_server_seq"],
                            "has_more": sync_result["has_more"],
                            "server_ts_ms": _now_ms(),
                        },
                        trace_id=envelope.trace_id,
                        correlation_event_id=envelope.event_id,
                    )
                )
                continue

            if event_type in {"typing.started", "typing.stopped"}:
                try:
                    typing_payload = TypingPayload.model_validate(envelope.payload)
                except ValidationError as exc:
                    await _send_error(
                        websocket=websocket,
                        code="INVALID_TYPING_EVENT",
                        message=exc.errors()[0]["msg"],
                        retryable=False,
                        trace_id=envelope.trace_id,
                        correlation_event_id=envelope.event_id,
                    )
                    continue
                # TODO(systemforge-realtime): Publish typing.updated to conversation members via realtime stream.
                await websocket.send_json(
                    _build_event(
                        event_type="ack",
                        payload={
                            "received_type": event_type,
                            "conversation_id": typing_payload.conversation_id,
                            "received_at_ms": _now_ms(),
                        },
                        trace_id=envelope.trace_id,
                        correlation_event_id=envelope.event_id,
                    )
                )
                continue

            await _send_error(
                websocket=websocket,
                code="UNSUPPORTED_EVENT",
                message=f"Unsupported event type: {event_type}",
                retryable=False,
                trace_id=envelope.trace_id,
                correlation_event_id=envelope.event_id,
            )
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("ws_unhandled_exception", extra={"user_id": user.id, "socket_id": socket_id})
    finally:
        forwarder_task.cancel()
        try:
            await forwarder_task
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("ws_stream_forwarder_shutdown_failed", extra={"user_id": user.id, "socket_id": socket_id})
        try:
            await presence_service.redis.xgroup_destroy(user_stream, ws_group)
        except Exception:
            pass
        await connection_manager.disconnect(socket_id=socket_id)
        try:
            await presence_service.unregister_session(user_id=user.id, socket_id=socket_id)
        except Exception:
            logger.exception("ws_presence_disconnect_failed", extra={"user_id": user.id, "socket_id": socket_id})
        logger.info("ws_disconnected", extra={"user_id": user.id, "socket_id": socket_id})
