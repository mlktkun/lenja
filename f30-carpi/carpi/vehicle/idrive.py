"""Dekodiert iDrive-Controller- und Lenkradtasten-Botschaften vom K-CAN.

Die CAN-IDs und Bytepositionen des F30 sind nicht öffentlich dokumentiert.
Sie stehen deshalb nicht im Code, sondern in config/idrive_map.toml und
werden mit tools/can_sniff.py am eigenen Auto ermittelt.

Ausgabe sind Navigationsereignisse für die Oberfläche:

    {"type": "nav", "action": "rotate", "delta": +1}
    {"type": "nav", "action": "press", "button": "enter"}
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from ..events import Event


@dataclass(frozen=True)
class RotarySpec:
    can_id: int
    byte: int
    width: int = 1  # 1 oder 2 Bytes (little endian)
    invert: bool = False


@dataclass(frozen=True)
class ButtonSpec:
    name: str
    can_id: int
    byte: int
    mask: int
    value: int


@dataclass
class IDriveMap:
    rotary: RotarySpec | None = None
    buttons: list[ButtonSpec] = field(default_factory=list)

    @classmethod
    def load(cls, path: Path) -> IDriveMap:
        if not path.exists():
            return cls()
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        rotary = None
        if "rotary" in data and data["rotary"].get("can_id") is not None:
            r = data["rotary"]
            rotary = RotarySpec(
                can_id=int(r["can_id"]),
                byte=int(r["byte"]),
                width=int(r.get("width", 1)),
                invert=bool(r.get("invert", False)),
            )
        buttons = [
            ButtonSpec(
                name=b["name"],
                can_id=int(b["can_id"]),
                byte=int(b["byte"]),
                mask=int(b.get("mask", 0xFF)),
                value=int(b["value"]),
            )
            for b in data.get("buttons", [])
        ]
        return cls(rotary=rotary, buttons=buttons)

    @property
    def can_ids(self) -> set[int]:
        ids = {b.can_id for b in self.buttons}
        if self.rotary:
            ids.add(self.rotary.can_id)
        return ids


class IDriveDecoder:
    """Wandelt einzelne CAN-Frames in Navigationsereignisse um (zustandsbehaftet)."""

    def __init__(self, mapping: IDriveMap) -> None:
        self.mapping = mapping
        self._last_counter: int | None = None
        self._pressed: set[str] = set()

    def feed(self, can_id: int, data: bytes) -> list[Event]:
        events: list[Event] = []
        rotary = self.mapping.rotary
        if rotary and can_id == rotary.can_id:
            delta = self._rotary_delta(rotary, data)
            if delta:
                events.append({"type": "nav", "action": "rotate", "delta": delta})

        for button in self.mapping.buttons:
            if can_id != button.can_id or len(data) <= button.byte:
                continue
            active = (data[button.byte] & button.mask) == button.value
            # Flankenerkennung: nur beim Drücken melden, nicht bei jeder Wiederholung
            if active and button.name not in self._pressed:
                self._pressed.add(button.name)
                events.append({"type": "nav", "action": "press", "button": button.name})
            elif not active:
                self._pressed.discard(button.name)
        return events

    def _rotary_delta(self, spec: RotarySpec, data: bytes) -> int:
        if len(data) < spec.byte + spec.width:
            return 0
        counter = int.from_bytes(data[spec.byte : spec.byte + spec.width], "little")
        last, self._last_counter = self._last_counter, counter
        if last is None:
            return 0
        modulo = 1 << (8 * spec.width)
        delta = (counter - last) % modulo
        if delta > modulo // 2:  # Überlauf rückwärts
            delta -= modulo
        return -delta if spec.invert else delta
