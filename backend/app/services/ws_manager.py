import asyncio
from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.connections: dict[int, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        async with self._lock:
            self.connections[user_id].add(websocket)

    async def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        async with self._lock:
            self.connections[user_id].discard(websocket)
            if not self.connections[user_id]:
                self.connections.pop(user_id, None)

    async def send_to_user(self, user_id: int, data: dict) -> None:
        async with self._lock:
            sockets = list(self.connections.get(user_id, set()))
        for socket in sockets:
            try:
                await socket.send_json(data)
            except (RuntimeError, OSError):
                await self.disconnect(user_id, socket)


manager = ConnectionManager()
