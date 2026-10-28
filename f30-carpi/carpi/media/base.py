"""Schnittstelle für Medien."""

from __future__ import annotations

from typing import Any, Protocol

MEDIA_ACTIONS = ("play", "pause", "next", "previous")


class MediaService(Protocol):
    async def control(self, action: str) -> None: ...

    async def play_search(self, query: str) -> str | None:
        """Sucht Titel/Interpret/Album und spielt den ersten Treffer. Gibt den Titel zurück."""
        ...

    async def now_playing(self) -> dict[str, Any]: ...

    async def set_volume(self, percent: int) -> None: ...
