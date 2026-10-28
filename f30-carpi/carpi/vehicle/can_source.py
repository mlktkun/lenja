"""Liest CAN-Frames vom echten Bus (SocketCAN) oder aus einer Log-Datei.

Sicherheit: Der Pi soll den Fahrzeugbus nur mitlesen. Die Schnittstelle wird
deshalb auf Betriebssystemebene im listen-only-Modus konfiguriert (siehe
deploy/can0.network) und hier ausschließlich empfangen – es gibt bewusst
keine Sendefunktion.
"""

from __future__ import annotations

import asyncio
import logging

import can

from ..config import Settings
from ..events import EventBus
from .idrive import IDriveDecoder, IDriveMap

log = logging.getLogger(__name__)


async def run_can_reader(settings: Settings, bus: EventBus) -> None:
    decoder = IDriveDecoder(IDriveMap.load(settings.idrive_map))
    if not decoder.mapping.can_ids:
        log.warning("idrive_map ist leer – iDrive-Bedienung erst nach dem Sniffen (tools/can_sniff.py)")

    if settings.can_replay:
        await _replay(settings.can_replay, decoder, bus)
        return

    if not settings.is_car:
        log.info("sim-Modus: kein CAN-Bus, iDrive per Tastatur in der Oberfläche")
        return

    while True:
        try:
            await _read_live(settings, decoder, bus)
        except (can.CanError, OSError) as exc:
            log.error("CAN-Fehler: %s – neuer Versuch in 5 s", exc)
            await asyncio.sleep(5)


async def _read_live(settings: Settings, decoder: IDriveDecoder, bus: EventBus) -> None:
    filters = [{"can_id": i, "can_mask": 0x7FF} for i in decoder.mapping.can_ids] or None
    with can.Bus(interface=settings.can_interface, channel=settings.can_channel, can_filters=filters) as can_bus:
        reader = can.AsyncBufferedReader()
        notifier = can.Notifier(can_bus, [reader], loop=asyncio.get_running_loop())
        try:
            async for msg in reader:
                _dispatch(decoder, bus, msg)
        finally:
            notifier.stop()


async def _replay(path: str, decoder: IDriveDecoder, bus: EventBus) -> None:
    log.info("spiele CAN-Log ab: %s", path)
    for msg in can.MessageSync(can.LogReader(path)):
        _dispatch(decoder, bus, msg)
        await asyncio.sleep(0)


def _dispatch(decoder: IDriveDecoder, bus: EventBus, msg: can.Message) -> None:
    for event in decoder.feed(msg.arbitration_id, bytes(msg.data)):
        bus.publish(event)
