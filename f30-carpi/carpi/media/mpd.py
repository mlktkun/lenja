"""Musik über MPD (Music Player Daemon) – lokale Bibliothek auf SSD/USB-Stick.

Streamingdienste: z. B. librespot (Spotify Connect) oder Musik vom Handy
per Bluetooth-A2DP; diese laufen als eigene Dienste neben MPD.
"""

from __future__ import annotations

from typing import Any

from ..events import EventBus
from .base import MEDIA_ACTIONS


class MpdMedia:
    def __init__(self, bus: EventBus, host: str, port: int) -> None:
        from mpd.asyncio import MPDClient

        self._bus = bus
        self._host, self._port = host, port
        self._client = MPDClient()
        self._connected = False

    async def _mpd(self):
        if not self._connected:
            await self._client.connect(self._host, self._port)
            self._connected = True
        return self._client

    async def _publish(self) -> None:
        self._bus.publish({"type": "media.state", **(await self.now_playing())})

    async def control(self, action: str) -> None:
        if action not in MEDIA_ACTIONS:
            raise ValueError(f"unbekannte Aktion: {action}")
        mpd = await self._mpd()
        if action == "pause":
            await mpd.pause(1)
        else:
            await getattr(mpd, action)()
        await self._publish()

    async def play_search(self, query: str) -> str | None:
        mpd = await self._mpd()
        hits = await mpd.search("any", query)
        if not hits:
            return None
        await mpd.clear()
        for song in hits[:50]:
            await mpd.add(song["file"])
        await mpd.play(0)
        await self._publish()
        first = hits[0]
        return f"{first.get('artist', '?')} – {first.get('title', first['file'])}"

    async def now_playing(self) -> dict[str, Any]:
        mpd = await self._mpd()
        song, status = await mpd.currentsong(), await mpd.status()
        return {
            "playing": status.get("state") == "play",
            "volume": int(status.get("volume", 0)),
            "title": song.get("title", ""),
            "artist": song.get("artist", ""),
        }

    async def set_volume(self, percent: int) -> None:
        mpd = await self._mpd()
        await mpd.setvol(max(0, min(100, percent)))
        await self._publish()
