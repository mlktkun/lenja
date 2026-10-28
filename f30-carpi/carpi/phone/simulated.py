"""Simuliertes Handy für die Entwicklung am PC."""

from __future__ import annotations

from ..events import EventBus
from .base import Contact

DEMO_CONTACTS = [
    Contact("Anna Becker", "+49 151 1111111"),
    Contact("Werkstatt Müller", "+49 30 2222222"),
    Contact("Mama", "+49 160 3333333"),
]


class SimulatedPhone:
    def __init__(self, bus: EventBus, contacts: list[Contact] | None = None) -> None:
        self._bus = bus
        self._contacts = list(DEMO_CONTACTS if contacts is None else contacts)
        self.sent_sms: list[tuple[str, str]] = []
        self.active_number: str | None = None

    async def dial(self, number: str) -> None:
        self.active_number = number
        self._bus.publish({"type": "phone.call", "state": "dialing", "number": number})

    async def hangup(self) -> None:
        if self.active_number:
            self._bus.publish({"type": "phone.call", "state": "ended", "number": self.active_number})
        self.active_number = None

    async def answer(self) -> None:
        if self.active_number:
            self._bus.publish({"type": "phone.call", "state": "active", "number": self.active_number})

    async def send_sms(self, number: str, text: str) -> None:
        self.sent_sms.append((number, text))
        self._bus.publish({"type": "phone.sms_sent", "number": number})

    async def contacts(self) -> list[Contact]:
        return list(self._contacts)
