"""Bordassistent auf Basis der Claude-API mit eigenen Werkzeugen.

- Modell, Effort usw. kommen aus Settings (CARPI_MODEL, CARPI_EFFORT).
- Effort "low" hält die Antwortzeit im Auto kurz.
- Server-seitige Fallbacks ("default") sind aktiv: Lehnt das Modell eine
  Anfrage aus Sicherheitsgründen ab, beantwortet die API sie automatisch mit
  einem Ausweichmodell, statt einfach abzubrechen.
- Die Unterhaltung wird nie nachträglich verändert, nur ergänzt. Nach
  längerer Pause (agent_idle_reset_s) beginnt eine neue Unterhaltung.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import anthropic

from ..config import Settings
from ..events import EventBus
from .tools import TOOL_DEFINITIONS, Toolbox

log = logging.getLogger(__name__)

MAX_STEPS = 8

SYSTEM_PROMPT = """\
Du bist der Bordassistent in einem BMW 3er (F30). Der Fahrer spricht mit dir, \
während er fährt. Deine Antworten werden vorgelesen.

- Antworte auf Deutsch, kurz (meist ein bis drei Sätze) und gut vorlesbar: \
kein Markdown, keine Listen, keine Links, Zahlen so, wie man sie spricht.
- Nutze die Werkzeuge, um Anrufe, SMS und Musik zu steuern. Wenn der Fahrer \
nur einen Namen nennt, suche zuerst den Kontakt. Bei mehreren Treffern frage \
kurz nach.
- Lies eine SMS vor dem Senden mit Empfänger und Text vor und sende sie erst \
nach ausdrücklicher Bestätigung.
- Für aktuelle Informationen (Wetter, Öffnungszeiten, Nachrichten) darfst du \
die Websuche nutzen, falls verfügbar.
- Lenke den Fahrer nicht ab: keine langen Erklärungen, keine Rückfragen ohne Not.
"""


class CarAgent:
    def __init__(
        self,
        settings: Settings,
        toolbox: Toolbox,
        bus: EventBus,
        client: anthropic.AsyncAnthropic | None = None,
    ) -> None:
        self.settings = settings
        self.toolbox = toolbox
        self.bus = bus
        self.client = client or anthropic.AsyncAnthropic()
        self.messages: list[dict[str, Any]] = []
        self._last_activity = 0.0
        self._lock = asyncio.Lock()
        self.tools: list[dict[str, Any]] = list(TOOL_DEFINITIONS)
        if settings.web_search:
            self.tools.append(
                {
                    "type": "web_search_20260209",
                    "name": "web_search",
                    "max_uses": 3,
                    "user_location": {"type": "approximate", "country": "DE", "timezone": "Europe/Berlin"},
                }
            )

    def reset(self) -> None:
        self.messages = []
        self.bus.publish({"type": "agent.reset"})

    async def ask(self, text: str) -> str:
        # Fragen nacheinander abarbeiten, damit sich zwei Turns nicht vermischen
        async with self._lock:
            return await self._ask(text)

    async def _ask(self, text: str) -> str:
        now = time.monotonic()
        if self.messages and now - self._last_activity > self.settings.agent_idle_reset_s:
            self.reset()
        self._last_activity = now

        self.messages.append({"role": "user", "content": text})
        self.bus.publish({"type": "agent.question", "text": text})
        try:
            reply = await self._run_loop()
        except anthropic.APIConnectionError:
            reply = "Ich habe gerade keine Internetverbindung."
            self.reset()
        except anthropic.RateLimitError:
            reply = "Ich bin gerade überlastet. Versuch es gleich noch einmal."
            self.reset()
        except anthropic.APIStatusError as exc:
            log.error("Claude-API-Fehler %s: %s", exc.status_code, exc.message)
            reply = "Da ist etwas schiefgelaufen."
            self.reset()
        except anthropic.AnthropicError as exc:  # z. B. kein API-Schlüssel hinterlegt
            log.error("Claude-Client-Fehler: %s", exc)
            reply = "Der Assistent ist nicht eingerichtet."
            self.reset()
        self.bus.publish({"type": "agent.reply", "text": reply})
        return reply

    async def _run_loop(self) -> str:
        for _ in range(MAX_STEPS):
            response = await self.client.beta.messages.create(
                model=self.settings.model,
                max_tokens=16000,
                system=SYSTEM_PROMPT,
                tools=self.tools,
                messages=self.messages,
                thinking={"type": "adaptive"},
                output_config={"effort": self.settings.effort},
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )

            if response.stop_reason == "refusal":
                self.reset()
                return "Dabei kann ich leider nicht helfen."

            self.messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "pause_turn":
                continue  # Websuche läuft noch: Turn unverändert zurückschicken
            if response.stop_reason != "tool_use":
                return _text_of(response.content) or "Erledigt."

            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                self.bus.publish({"type": "agent.tool", "name": block.name, "input": block.input})
                result, is_error = await self.toolbox.run(block.name, block.input)
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": result, "is_error": is_error}
                )
            # Alle Ergebnisse gemeinsam in einer Nachricht zurückgeben
            self.messages.append({"role": "user", "content": tool_results})

        self.reset()
        return "Das hat zu lange gedauert. Bitte noch einmal anders fragen."


def _text_of(content: list[Any]) -> str:
    return " ".join(block.text for block in content if block.type == "text").strip()
