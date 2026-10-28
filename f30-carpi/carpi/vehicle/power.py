"""Bordnetz überwachen und den Pi sauber herunterfahren (CarPiHAT).

Im F30 gibt es kein klassisches Zündungsplus (Klemme 15 ist nur virtuell auf
dem Bus). Der "Zündungs"-Eingang des CarPiHAT hängt deshalb an einer
geschalteten Sicherung mit Klemme 15N (Nachlauf) oder 30B (Fahrzeug wach),
siehe docs/BAUPLAN.md. Den genauen Zündungszustand liefert zusätzlich der
CAN-Decoder (Ereignis vehicle.ignition mit source="can").

Ablauf beim CarPiHAT: Die Platine schaltet den Pi bei Spannung am Eingang ein. Der Pi
hält danach einen "Latch"-Ausgang auf HIGH. Fällt die Zündung weg, wartet
er shutdown_delay_s (kurzer Tankstopp), fährt dann herunter und lässt den
Latch los – danach ist der Pi stromlos. GPIO-Nummern laut HAT-Doku prüfen.
"""

from __future__ import annotations

import asyncio
import logging
import subprocess

from ..config import Settings
from ..events import EventBus

log = logging.getLogger(__name__)


async def run_power_monitor(settings: Settings, bus: EventBus) -> None:
    if not settings.is_car:
        return
    try:
        from gpiozero import DigitalInputDevice, DigitalOutputDevice
    except ImportError:
        log.error("gpiozero fehlt – Zündungsüberwachung inaktiv (pip install '.[car]')")
        return

    latch = DigitalOutputDevice(settings.power_latch_gpio, initial_value=True)
    ignition = DigitalInputDevice(settings.ignition_gpio)
    off_since: float | None = None
    loop = asyncio.get_running_loop()
    last_state: bool | None = None

    while True:
        on = bool(ignition.value)
        if on != last_state:
            bus.publish({"type": "vehicle.power", "on": on, "source": "gpio"})
            last_state = on
        if on:
            off_since = None
        elif off_since is None:
            off_since = loop.time()
            log.info("Bordnetz-Eingang aus – Herunterfahren in %.0f s", settings.shutdown_delay_s)
        elif loop.time() - off_since >= settings.shutdown_delay_s:
            bus.publish({"type": "system.shutdown"})
            log.warning("fahre herunter")
            # Der Latch-Pin fällt beim Halt ab, sobald dieser Prozess beendet ist; zuverlässiger
            # ist das Kernel-Overlay "gpio-poweroff" in /boot/firmware/config.txt (siehe README).
            subprocess.run(["sudo", "systemctl", "poweroff"], check=False)
            return
        await asyncio.sleep(0.5)
