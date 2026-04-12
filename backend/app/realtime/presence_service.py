from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from redis.asyncio import Redis

from app.core.config import get_settings
from app.core.redis import get_redis_client


@dataclass(frozen=True)
class PresenceState:
    user_id: int
    status: str
    last_heartbeat_ms: int | None
    last_seen_ms: int | None
    active_sessions: int


def _now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


class PresenceService:
    """
    Manages online/offline and websocket session state in Redis.

    Key model:
      - sf:rt:v1:presence:user:{user_id}   (HASH)
      - sf:rt:v1:user:sockets:{user_id}    (SET)
      - sf:rt:v1:socket:{socket_id}        (HASH)
    """

    def __init__(
        self,
        redis_client: Redis | None = None,
        *,
        presence_ttl_seconds: int = 75,
        socket_ttl_seconds: int = 75,
        user_sockets_ttl_seconds: int = 120,
    ) -> None:
        settings = get_settings()
        self.redis = redis_client or get_redis_client()
        self.key_prefix = "sf:rt:v1"
        self.presence_ttl_seconds = max(15, presence_ttl_seconds)
        self.socket_ttl_seconds = max(15, socket_ttl_seconds)
        self.user_sockets_ttl_seconds = max(self.socket_ttl_seconds, user_sockets_ttl_seconds)
        # keep heartbeat interval lower than key TTL to avoid false-offline.
        self.heartbeat_recommended_seconds = 25 if settings.app_env != "test" else 5

    def _presence_key(self, user_id: int) -> str:
        return f"{self.key_prefix}:presence:user:{user_id}"

    def _user_sockets_key(self, user_id: int) -> str:
        return f"{self.key_prefix}:user:sockets:{user_id}"

    def _socket_key(self, socket_id: str) -> str:
        return f"{self.key_prefix}:socket:{socket_id}"

    async def register_session(
        self,
        *,
        user_id: int,
        socket_id: str,
        device_id: str | None = None,
        platform: str | None = None,
        app_version: str | None = None,
        ip_hash: str | None = None,
    ) -> None:
        now_ms = str(_now_ms())
        user_sockets_key = self._user_sockets_key(user_id)
        socket_key = self._socket_key(socket_id)
        presence_key = self._presence_key(user_id)

        socket_meta: dict[str, str] = {
            "user_id": str(user_id),
            "connected_at_ms": now_ms,
            "last_heartbeat_ms": now_ms,
        }
        if device_id:
            socket_meta["device_id"] = device_id
        if platform:
            socket_meta["platform"] = platform
        if app_version:
            socket_meta["app_version"] = app_version
        if ip_hash:
            socket_meta["ip_hash"] = ip_hash

        async with self.redis.pipeline(transaction=True) as pipe:
            await (
                pipe.sadd(user_sockets_key, socket_id)
                .expire(user_sockets_key, self.user_sockets_ttl_seconds)
                .hset(socket_key, mapping=socket_meta)
                .expire(socket_key, self.socket_ttl_seconds)
                .hset(
                    presence_key,
                    mapping={
                        "status": "online",
                        "last_heartbeat_ms": now_ms,
                    },
                )
                .expire(presence_key, self.presence_ttl_seconds)
                .execute()
            )

    async def heartbeat(
        self,
        *,
        user_id: int,
        socket_id: str,
        status: str = "online",
    ) -> bool:
        if status not in {"online", "away"}:
            status = "online"

        socket_key = self._socket_key(socket_id)
        user_sockets_key = self._user_sockets_key(user_id)
        presence_key = self._presence_key(user_id)
        now_ms = str(_now_ms())

        exists = await self.redis.exists(socket_key)
        if not exists:
            return False

        async with self.redis.pipeline(transaction=True) as pipe:
            await (
                pipe.hset(socket_key, mapping={"last_heartbeat_ms": now_ms})
                .expire(socket_key, self.socket_ttl_seconds)
                .expire(user_sockets_key, self.user_sockets_ttl_seconds)
                .hset(
                    presence_key,
                    mapping={
                        "status": status,
                        "last_heartbeat_ms": now_ms,
                    },
                )
                .expire(presence_key, self.presence_ttl_seconds)
                .execute()
            )
        return True

    async def unregister_session(self, *, user_id: int, socket_id: str) -> None:
        user_sockets_key = self._user_sockets_key(user_id)
        socket_key = self._socket_key(socket_id)
        presence_key = self._presence_key(user_id)

        async with self.redis.pipeline(transaction=True) as pipe:
            await pipe.srem(user_sockets_key, socket_id).delete(socket_key).execute()

        remaining = int(await self.redis.scard(user_sockets_key))
        if remaining <= 0:
            now_ms = str(_now_ms())
            async with self.redis.pipeline(transaction=True) as pipe:
                await (
                    pipe.hset(
                        presence_key,
                        mapping={
                            "status": "offline",
                            "last_seen_ms": now_ms,
                        },
                    )
                    .expire(presence_key, self.presence_ttl_seconds)
                    .delete(user_sockets_key)
                    .execute()
                )
        else:
            await self.redis.expire(user_sockets_key, self.user_sockets_ttl_seconds)

    async def active_socket_ids(self, *, user_id: int) -> list[str]:
        raw = await self.redis.smembers(self._user_sockets_key(user_id))
        return sorted(raw) if raw else []

    async def active_socket_count(self, *, user_id: int) -> int:
        return int(await self.redis.scard(self._user_sockets_key(user_id)))

    async def is_online(self, *, user_id: int) -> bool:
        presence = await self.redis.hgetall(self._presence_key(user_id))
        if not presence:
            return False
        if presence.get("status") not in {"online", "away"}:
            return False
        return await self.active_socket_count(user_id=user_id) > 0

    async def get_presence_state(self, *, user_id: int) -> PresenceState:
        presence = await self.redis.hgetall(self._presence_key(user_id))
        active_sessions = int(await self.redis.scard(self._user_sockets_key(user_id)))
        return PresenceState(
            user_id=user_id,
            status=presence.get("status", "offline"),
            last_heartbeat_ms=int(presence["last_heartbeat_ms"]) if "last_heartbeat_ms" in presence else None,
            last_seen_ms=int(presence["last_seen_ms"]) if "last_seen_ms" in presence else None,
            active_sessions=active_sessions,
        )

    def recommended_heartbeat_interval_seconds(self) -> int:
        return self.heartbeat_recommended_seconds


presence_service = PresenceService()
