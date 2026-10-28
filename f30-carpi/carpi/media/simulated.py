"""Simulierte Medienwiedergabe für die Entwicklung am PC."""

from __future__ import annotations

from typing import Any

from ..events import EventBus
from .base import MEDIA_ACTIONS

DEMO_LIBRARY = [
    {"title": "Autobahn", "artist": "Kraftwerk"},
    {"title": "Major Tom", "artist": "Peter Schilling"},
    {"title": "Bohemian Rhapsody", "artist": "Queen"},
]


class SimulatedMedia:
    def __init__(self, bus: EventBus) -> None:
        self._bus = bus
        self._index = 0
        self._playing = False
        self.volume = 50

    def _publish(self) -> None:
        self._bus.publish({"type": "media.state", **self._state()})

    def _state(self) -> dict[str, Any]:
        track = DEMO_LIBRARY[self._index]
        return {"playing": self._playing, "volume": self.volume, **track}

    async def control(self, action: str) -> None:
        if action not in MEDIA_ACTIONS:
            raise ValueError(f"unbekannte Aktion: {action}")
        if action == "play":
            self._playing = True
        elif action == "pause":
            self._playing = False
        elif action == "next":
            self._index = (self._index + 1) % len(DEMO_LIBRARY)
        elif action == "previous":
            self._index = (self._index - 1) % len(DEMO_LIBRARY)
        self._publish()

    async def play_search(self, query: str) -> str | None:
        q = query.casefold()
        for i, track in enumerate(DEMO_LIBRARY):
            if q in track["title"].casefold() or q in track["artist"].casefold():
                self._index, self._playing = i, True
                self._publish()
                return f"{track['artist']} – {track['title']}"
        return None

    async def now_playing(self) -> dict[str, Any]:
        return self._state()

    async def set_volume(self, percent: int) -> None:
        self.volume = max(0, min(100, percent))
        self._publish()
