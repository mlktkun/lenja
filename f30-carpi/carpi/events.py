"""Einfacher asynchroner Ereignisbus.

Alle Module (Fahrzeug, Telefon, Medien, Agent) und die Oberfläche tauschen
Ereignisse als dicts mit einem Feld "type" aus, z. B.:

    {"type": "nav", "action": "rotate", "delta": 1}
    {"type": "phone.call", "state": "active", "number": "+49..."}
    {"type": "agent.reply", "text": "..."}
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator
from typing import Any

log = logging.getLogger(__name__)

Event = dict[str, Any]


class EventBus:
    def __init__(self, queue_size: int = 256) -> None:
        self._subscribers: set[asyncio.Queue[Event]] = set()
        self._queue_size = queue_size

    def publish(self, event: Event) -> None:
        if "type" not in event:
            raise ValueError("event needs a 'type'")
        for queue in list(self._subscribers):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                # Langsamer Abnehmer (z. B. hängender Browser): ältestes Ereignis verwerfen
                with contextlib.suppress(asyncio.QueueEmpty):
                    queue.get_nowait()
                queue.put_nowait(event)
                log.warning("event queue full, dropped oldest event")

    @contextlib.asynccontextmanager
    async def subscribe(self) -> AsyncIterator[asyncio.Queue[Event]]:
        queue: asyncio.Queue[Event] = asyncio.Queue(self._queue_size)
        self._subscribers.add(queue)
        try:
            yield queue
        finally:
            self._subscribers.discard(queue)
