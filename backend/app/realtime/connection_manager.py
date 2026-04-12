import asyncio
from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    """Tracks active websocket connections by socket and user IDs."""

    def __init__(self) -> None:
        self._socket_to_ws: dict[str, WebSocket] = {}
        self._socket_to_user: dict[str, int] = {}
        self._user_to_sockets: dict[int, set[str]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, *, user_id: int, socket_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            self._socket_to_ws[socket_id] = websocket
            self._socket_to_user[socket_id] = user_id
            self._user_to_sockets[user_id].add(socket_id)

    async def disconnect(self, *, socket_id: str) -> int | None:
        async with self._lock:
            websocket = self._socket_to_ws.pop(socket_id, None)
            user_id = self._socket_to_user.pop(socket_id, None)
            if user_id is not None:
                user_sockets = self._user_to_sockets.get(user_id)
                if user_sockets is not None:
                    user_sockets.discard(socket_id)
                    if not user_sockets:
                        self._user_to_sockets.pop(user_id, None)
            if websocket is not None:
                try:
                    await websocket.close()
                except Exception:
                    pass
            return user_id

    async def socket_ids_for_user(self, *, user_id: int) -> list[str]:
        async with self._lock:
            return sorted(self._user_to_sockets.get(user_id, set()))

    async def send_to_socket(self, *, socket_id: str, payload: dict) -> bool:
        websocket = self._socket_to_ws.get(socket_id)
        if websocket is None:
            return False
        try:
            await websocket.send_json(payload)
            return True
        except Exception:
            return False

    async def send_to_user(self, *, user_id: int, payload: dict) -> int:
        sent = 0
        for socket_id in list(self._user_to_sockets.get(user_id, set())):
            ok = await self.send_to_socket(socket_id=socket_id, payload=payload)
            if ok:
                sent += 1
        return sent

    async def has_active_socket(self, *, user_id: int) -> bool:
        async with self._lock:
            return bool(self._user_to_sockets.get(user_id))

    async def active_connections(self) -> int:
        async with self._lock:
            return len(self._socket_to_ws)


connection_manager = ConnectionManager()
