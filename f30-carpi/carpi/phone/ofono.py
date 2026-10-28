"""Telefonie über oFono (Bluetooth-HFP) per D-Bus.

Voraussetzungen auf dem Pi (siehe README):
- bluez, ofono, pipewire + wireplumber mit HFP-Backend "ofono"
- Handy einmalig mit `bluetoothctl` koppeln und vertrauen

Noch nicht am Auto getestet – erste Inbetriebnahme auf dem Prüfstand (Stufe 1).
Das Telefonbuch (PBAP über obexd) ist noch offen; bis dahin liefert
contacts() die Kontakte aus config/contacts.csv, falls vorhanden.
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path

from ..config import PROJECT_ROOT
from ..events import EventBus
from .base import Contact

log = logging.getLogger(__name__)

OFONO = "org.ofono"


class OfonoPhone:
    def __init__(self, bus: EventBus, contacts_csv: Path = PROJECT_ROOT / "config" / "contacts.csv") -> None:
        self._events = bus
        self._contacts_csv = contacts_csv
        self._dbus = None

    async def _modem(self) -> str:
        from dbus_fast import BusType
        from dbus_fast.aio import MessageBus

        if self._dbus is None:
            self._dbus = await MessageBus(bus_type=BusType.SYSTEM).connect()
        manager = await self._interface("/", "org.ofono.Manager")
        modems = await manager.call_get_modems()
        for path, props in modems:
            if props.get("Online") and props["Online"].value:
                return path
        raise RuntimeError("Kein verbundenes Handy (oFono-Modem offline)")

    async def _interface(self, path: str, name: str):
        introspection = await self._dbus.introspect(OFONO, path)
        return self._dbus.get_proxy_object(OFONO, path, introspection).get_interface(name)

    async def dial(self, number: str) -> None:
        calls = await self._interface(await self._modem(), "org.ofono.VoiceCallManager")
        await calls.call_dial(number, "default")
        self._events.publish({"type": "phone.call", "state": "dialing", "number": number})

    async def hangup(self) -> None:
        calls = await self._interface(await self._modem(), "org.ofono.VoiceCallManager")
        await calls.call_hangup_all()
        self._events.publish({"type": "phone.call", "state": "ended"})

    async def answer(self) -> None:
        modem = await self._modem()
        calls = await self._interface(modem, "org.ofono.VoiceCallManager")
        for path, props in await calls.call_get_calls():
            if props["State"].value == "incoming":
                call = await self._interface(path, "org.ofono.VoiceCall")
                await call.call_answer()
                self._events.publish({"type": "phone.call", "state": "active"})
                return

    async def send_sms(self, number: str, text: str) -> None:
        messages = await self._interface(await self._modem(), "org.ofono.MessageManager")
        await messages.call_send_message(number, text)
        self._events.publish({"type": "phone.sms_sent", "number": number})

    async def contacts(self) -> list[Contact]:
        if not self._contacts_csv.exists():
            return []
        with self._contacts_csv.open(encoding="utf-8", newline="") as f:
            return [Contact(row["name"], row["number"]) for row in csv.DictReader(f)]
