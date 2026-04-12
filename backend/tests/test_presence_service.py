import copy

import pytest

from app.realtime.presence_service import PresenceService


class FakeRedisPipeline:
    def __init__(self, redis: "FakeRedis"):
        self.redis = redis
        self.ops: list[tuple[str, tuple, dict]] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def sadd(self, key: str, value: str):
        self.ops.append(("sadd", (key, value), {}))
        return self

    def srem(self, key: str, value: str):
        self.ops.append(("srem", (key, value), {}))
        return self

    def expire(self, key: str, ttl_seconds: int):
        self.ops.append(("expire", (key, ttl_seconds), {}))
        return self

    def hset(self, key: str, mapping: dict):
        self.ops.append(("hset", (key, mapping), {}))
        return self

    def delete(self, key: str):
        self.ops.append(("delete", (key,), {}))
        return self

    async def execute(self):
        results = []
        for op, args, kwargs in self.ops:
            method = getattr(self.redis, f"_op_{op}")
            results.append(await method(*args, **kwargs))
        self.ops.clear()
        return results


class FakeRedis:
    def __init__(self):
        self.hash_data: dict[str, dict[str, str]] = {}
        self.set_data: dict[str, set[str]] = {}
        self.ttl_data: dict[str, int] = {}

    def pipeline(self, transaction: bool = True):
        return FakeRedisPipeline(self)

    async def _op_sadd(self, key: str, value: str):
        self.set_data.setdefault(key, set()).add(value)
        return 1

    async def _op_srem(self, key: str, value: str):
        if key in self.set_data:
            self.set_data[key].discard(value)
        return 1

    async def _op_expire(self, key: str, ttl_seconds: int):
        self.ttl_data[key] = ttl_seconds
        return True

    async def _op_hset(self, key: str, mapping: dict):
        current = self.hash_data.setdefault(key, {})
        for k, v in mapping.items():
            current[str(k)] = str(v)
        return len(mapping)

    async def _op_delete(self, key: str):
        self.hash_data.pop(key, None)
        self.set_data.pop(key, None)
        self.ttl_data.pop(key, None)
        return 1

    async def exists(self, key: str):
        return int(key in self.hash_data or key in self.set_data)

    async def scard(self, key: str):
        return len(self.set_data.get(key, set()))

    async def smembers(self, key: str):
        return copy.copy(self.set_data.get(key, set()))

    async def hgetall(self, key: str):
        return copy.copy(self.hash_data.get(key, {}))

    async def srem(self, key: str, value: str):
        return await self._op_srem(key, value)

    async def delete(self, key: str):
        return await self._op_delete(key)

    async def expire(self, key: str, ttl_seconds: int):
        return await self._op_expire(key, ttl_seconds)

    async def hset(self, key: str, mapping: dict):
        return await self._op_hset(key, mapping)


@pytest.mark.asyncio
async def test_presence_register_heartbeat_unregister_flow():
    redis = FakeRedis()
    service = PresenceService(redis_client=redis, presence_ttl_seconds=75, socket_ttl_seconds=75, user_sockets_ttl_seconds=120)
    user_id = 42
    socket_id = "skt_1"

    await service.register_session(user_id=user_id, socket_id=socket_id, device_id="web-1", platform="web")

    presence_key = f"sf:rt:v1:presence:user:{user_id}"
    socket_key = f"sf:rt:v1:socket:{socket_id}"
    user_sockets_key = f"sf:rt:v1:user:sockets:{user_id}"

    assert redis.hash_data[presence_key]["status"] == "online"
    assert redis.hash_data[socket_key]["user_id"] == str(user_id)
    assert socket_id in redis.set_data[user_sockets_key]
    assert redis.ttl_data[presence_key] == 75
    assert redis.ttl_data[socket_key] == 75
    assert redis.ttl_data[user_sockets_key] == 120

    ok = await service.heartbeat(user_id=user_id, socket_id=socket_id, status="away")
    assert ok is True
    assert redis.hash_data[presence_key]["status"] == "away"

    await service.unregister_session(user_id=user_id, socket_id=socket_id)
    assert socket_key not in redis.hash_data
    assert user_sockets_key not in redis.set_data
    assert redis.hash_data[presence_key]["status"] == "offline"
    assert "last_seen_ms" in redis.hash_data[presence_key]


@pytest.mark.asyncio
async def test_presence_heartbeat_rejects_unknown_socket():
    redis = FakeRedis()
    service = PresenceService(redis_client=redis)
    ok = await service.heartbeat(user_id=1, socket_id="missing")
    assert ok is False


@pytest.mark.asyncio
async def test_presence_online_and_active_sessions_queries():
    redis = FakeRedis()
    service = PresenceService(redis_client=redis)
    user_id = 7
    s1 = "skt_a"
    s2 = "skt_b"

    await service.register_session(user_id=user_id, socket_id=s1)
    await service.register_session(user_id=user_id, socket_id=s2)
    assert await service.is_online(user_id=user_id) is True

    socket_ids = await service.active_socket_ids(user_id=user_id)
    assert socket_ids == [s1, s2]

    state = await service.get_presence_state(user_id=user_id)
    assert state.status == "online"
    assert state.active_sessions == 2

    await service.unregister_session(user_id=user_id, socket_id=s1)
    state_after_one = await service.get_presence_state(user_id=user_id)
    assert state_after_one.status in {"online", "away"}
    assert state_after_one.active_sessions == 1

