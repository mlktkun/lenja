"""Web-Server: liefert die Oberfläche aus und verbindet sie per WebSocket mit dem Ereignisbus.

Befehle von der Oberfläche (JSON über /ws):

    {"cmd": "agent.ask", "text": "Ruf Mama an"}
    {"cmd": "agent.reset"}
    {"cmd": "media.control", "action": "next"}
    {"cmd": "media.volume", "percent": 40}
    {"cmd": "phone.dial", "number": "+49..."}
    {"cmd": "phone.hangup"} / {"cmd": "phone.answer"}
    {"cmd": "phone.contacts"}
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from .agent import CarAgent, Toolbox
from .config import Settings
from .events import EventBus
from .media import MediaService, SimulatedMedia
from .phone import PhoneService, SimulatedPhone
from .vehicle.can_source import run_can_reader
from .vehicle.power import run_power_monitor

log = logging.getLogger(__name__)

UI_DIR = Path(__file__).parent / "ui"


@dataclass
class Services:
    settings: Settings
    bus: EventBus
    phone: PhoneService
    media: MediaService
    agent: CarAgent | None


def build_services(settings: Settings, bus: EventBus | None = None, agent_client: Any = None) -> Services:
    bus = bus or EventBus()
    if settings.is_car:
        from .media.mpd import MpdMedia
        from .phone.ofono import OfonoPhone

        phone: PhoneService = OfonoPhone(bus)
        media: MediaService = MpdMedia(bus, settings.mpd_host, settings.mpd_port)
    else:
        phone = SimulatedPhone(bus)
        media = SimulatedMedia(bus)

    agent = None
    if agent_client is not None or os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        agent = CarAgent(settings, Toolbox(phone, media), bus, client=agent_client)
    else:
        log.warning("ANTHROPIC_API_KEY fehlt – Assistent deaktiviert")
    return Services(settings, bus, phone, media, agent)


def create_app(services: Services) -> FastAPI:
    background: list[asyncio.Task[None]] = []

    @contextlib.asynccontextmanager
    async def lifespan(_: FastAPI):
        background.append(asyncio.create_task(run_can_reader(services.settings, services.bus)))
        background.append(asyncio.create_task(run_power_monitor(services.settings, services.bus)))
        yield
        for task in background:
            task.cancel()

    app = FastAPI(title="f30-carpi", lifespan=lifespan)

    @app.get("/api/status")
    async def status() -> dict[str, Any]:
        return {
            "mode": services.settings.mode,
            "agent": services.agent is not None,
            "media": await _safe(services.media.now_playing()),
        }

    @app.websocket("/ws")
    async def ws(socket: WebSocket) -> None:
        await socket.accept()
        async with services.bus.subscribe() as queue:
            sender = asyncio.create_task(_forward(queue, socket))
            pending: set[asyncio.Task[None]] = set()
            try:
                while True:
                    command = await socket.receive_json()
                    task = asyncio.create_task(_handle(services, command, socket))
                    pending.add(task)
                    task.add_done_callback(pending.discard)
            except WebSocketDisconnect:
                pass
            finally:
                sender.cancel()

    app.mount("/", StaticFiles(directory=UI_DIR, html=True), name="ui")
    return app


async def _forward(queue: asyncio.Queue, socket: WebSocket) -> None:
    while True:
        await socket.send_json(await queue.get())


async def _safe(coro: Any) -> Any:
    try:
        return await coro
    except Exception as exc:
        return {"error": str(exc)}


async def _handle(services: Services, command: dict[str, Any], socket: WebSocket) -> None:
    cmd = command.get("cmd")
    bus = services.bus
    try:
        if cmd == "agent.ask":
            if services.agent is None:
                bus.publish({"type": "agent.question", "text": str(command.get("text", ""))})
                bus.publish({"type": "agent.reply", "text": "Der Assistent ist nicht eingerichtet (API-Schlüssel fehlt)."})
            else:
                await services.agent.ask(str(command.get("text", "")))
        elif cmd == "agent.reset" and services.agent:
            services.agent.reset()
        elif cmd == "media.control":
            await services.media.control(str(command["action"]))
        elif cmd == "media.volume":
            await services.media.set_volume(int(command["percent"]))
        elif cmd == "media.state":
            bus.publish({"type": "media.state", **(await services.media.now_playing())})
        elif cmd == "phone.dial":
            await services.phone.dial(str(command["number"]))
        elif cmd == "phone.hangup":
            await services.phone.hangup()
        elif cmd == "phone.answer":
            await services.phone.answer()
        elif cmd == "phone.contacts":
            contacts = await services.phone.contacts()
            await socket.send_json(
                {"type": "phone.contacts", "contacts": [{"name": c.name, "number": c.number} for c in contacts]}
            )
        else:
            log.warning("unbekannter Befehl: %s", command)
    except Exception as exc:
        log.exception("Befehl %s fehlgeschlagen", cmd)
        bus.publish({"type": "error", "cmd": cmd, "message": str(exc)})
