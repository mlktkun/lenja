"""Werkzeuge, die der Agent im Auto benutzen darf.

Neue Werkzeuge: Definition in TOOL_DEFINITIONS ergänzen und eine gleichnamige
Methode `tool_<name>` in Toolbox anlegen.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from ..media.base import MEDIA_ACTIONS, MediaService
from ..phone.base import PhoneService, find_contacts

log = logging.getLogger(__name__)


def _schema(properties: dict[str, Any] | None = None) -> dict[str, Any]:
    properties = properties or {}
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "search_contacts",
        "description": "Sucht im Telefonbuch des gekoppelten Handys nach einem Namen und liefert Name und Nummer.",
        "input_schema": _schema({"query": {"type": "string", "description": "Name oder Namensteil"}}),
    },
    {
        "name": "call",
        "description": "Startet einen Anruf über das gekoppelte Handy. Nummer vorher mit search_contacts ermitteln, falls nur ein Name genannt wurde.",
        "input_schema": _schema({"number": {"type": "string", "description": "Telefonnummer"}}),
    },
    {
        "name": "hang_up",
        "description": "Beendet das laufende Telefonat.",
        "input_schema": _schema(),
    },
    {
        "name": "send_sms",
        "description": "Sendet eine SMS. Nur aufrufen, nachdem der Fahrer Empfänger und Text ausdrücklich bestätigt hat.",
        "input_schema": _schema(
            {
                "number": {"type": "string", "description": "Telefonnummer des Empfängers"},
                "text": {"type": "string", "description": "Nachrichtentext"},
            }
        ),
    },
    {
        "name": "play_music",
        "description": "Sucht in der Musikbibliothek nach Titel, Interpret oder Album und spielt den Treffer ab.",
        "input_schema": _schema({"query": {"type": "string"}}),
    },
    {
        "name": "media_control",
        "description": "Steuert die laufende Wiedergabe.",
        "input_schema": _schema({"action": {"type": "string", "enum": list(MEDIA_ACTIONS)}}),
    },
    {
        "name": "set_volume",
        "description": "Setzt die Lautstärke der Wiedergabe des Bordcomputers in Prozent (0–100).",
        "input_schema": _schema({"percent": {"type": "integer"}}),
    },
    {
        "name": "now_playing",
        "description": "Liefert den aktuell laufenden Titel und den Wiedergabestatus.",
        "input_schema": _schema(),
    },
]

for _tool in TOOL_DEFINITIONS:
    _tool["strict"] = True


class Toolbox:
    def __init__(self, phone: PhoneService, media: MediaService) -> None:
        self.phone = phone
        self.media = media

    async def run(self, name: str, tool_input: dict[str, Any]) -> tuple[str, bool]:
        """Führt ein Werkzeug aus. Rückgabe: (Ergebnis als JSON-Text, is_error)."""
        handler = getattr(self, f"tool_{name}", None)
        if handler is None:
            return json.dumps({"error": f"unbekanntes Werkzeug {name}"}), True
        try:
            result = await handler(**tool_input)
        except Exception as exc:  # Fehler an den Agenten melden statt abzustürzen
            log.exception("Werkzeug %s fehlgeschlagen", name)
            return json.dumps({"error": str(exc)}, ensure_ascii=False), True
        return json.dumps(result, ensure_ascii=False), False

    async def tool_search_contacts(self, query: str) -> dict[str, Any]:
        hits = find_contacts(await self.phone.contacts(), query)
        return {"contacts": [{"name": c.name, "number": c.number} for c in hits]}

    async def tool_call(self, number: str) -> dict[str, Any]:
        await self.phone.dial(number)
        return {"status": "Anruf gestartet", "number": number}

    async def tool_hang_up(self) -> dict[str, Any]:
        await self.phone.hangup()
        return {"status": "aufgelegt"}

    async def tool_send_sms(self, number: str, text: str) -> dict[str, Any]:
        await self.phone.send_sms(number, text)
        return {"status": "gesendet", "number": number}

    async def tool_play_music(self, query: str) -> dict[str, Any]:
        title = await self.media.play_search(query)
        return {"status": "spielt", "track": title} if title else {"status": "nichts gefunden"}

    async def tool_media_control(self, action: str) -> dict[str, Any]:
        await self.media.control(action)
        return {"status": "ok", "action": action}

    async def tool_set_volume(self, percent: int) -> dict[str, Any]:
        await self.media.set_volume(percent)
        return {"status": "ok", "volume": max(0, min(100, percent))}

    async def tool_now_playing(self) -> dict[str, Any]:
        return await self.media.now_playing()
