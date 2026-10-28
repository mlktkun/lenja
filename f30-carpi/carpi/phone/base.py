"""Schnittstelle für Handyfunktionen.

Echte Umsetzung: BlueZ (Kopplung) + oFono (HFP: Anrufe, SMS) über D-Bus,
PipeWire für den Gesprächston, obexd/PBAP für das Telefonbuch.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Contact:
    name: str
    number: str


class PhoneService(Protocol):
    async def dial(self, number: str) -> None: ...

    async def hangup(self) -> None: ...

    async def answer(self) -> None: ...

    async def send_sms(self, number: str, text: str) -> None: ...

    async def contacts(self) -> list[Contact]: ...


def find_contacts(contacts: list[Contact], query: str, limit: int = 5) -> list[Contact]:
    """Einfache Namenssuche, unabhängig von Groß-/Kleinschreibung."""
    q = query.casefold().strip()
    if not q:
        return []
    exact = [c for c in contacts if c.name.casefold() == q]
    prefix = [c for c in contacts if c not in exact and c.name.casefold().startswith(q)]
    partial = [c for c in contacts if c not in exact and c not in prefix and q in c.name.casefold()]
    return (exact + prefix + partial)[:limit]
