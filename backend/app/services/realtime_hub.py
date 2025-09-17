from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, Dict, List
from uuid import UUID


class SessionRealtimeHub:
    def __init__(self) -> None:
        self._subscribers: Dict[UUID, List[asyncio.Queue[dict[str, Any]]]] = defaultdict(list)
        self._history: Dict[UUID, List[dict[str, Any]]] = defaultdict(list)
        self._lock = asyncio.Lock()
        self._max_history = 50

    async def subscribe(self, request_id: UUID) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        async with self._lock:
            self._subscribers[request_id].append(queue)
            history = list(self._history.get(request_id, []))
        for event in history:
            await queue.put(event)
        return queue

    async def unsubscribe(self, request_id: UUID, queue: asyncio.Queue[dict[str, Any]]) -> None:
        async with self._lock:
            subscribers = self._subscribers.get(request_id)
            if not subscribers:
                return
            try:
                subscribers.remove(queue)
            except ValueError:
                pass
            if not subscribers:
                self._subscribers.pop(request_id, None)
                self._history.pop(request_id, None)

    async def publish(self, request_id: UUID, event: dict[str, Any]) -> None:
        async with self._lock:
            subscribers = list(self._subscribers.get(request_id, []))
            history = self._history[request_id]
            history.append(event)
            if len(history) > self._max_history:
                history.pop(0)
        await asyncio.gather(*(subscriber.put(event) for subscriber in subscribers), return_exceptions=True)


def build_event(event_type: str, **data: Any) -> dict[str, Any]:
    return {"type": event_type, "data": data}


realtime_hub = SessionRealtimeHub()
