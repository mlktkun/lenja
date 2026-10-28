"""Einstellungen aus Umgebungsvariablen (CARPI_*)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _env(name: str, default: str) -> str:
    return os.environ.get(f"CARPI_{name}", default)


@dataclass(frozen=True)
class Settings:
    # "sim": läuft auf jedem PC ohne Auto-Hardware; "car": echte Hardware am Pi
    mode: str = field(default_factory=lambda: _env("MODE", "sim"))
    host: str = field(default_factory=lambda: _env("HOST", "127.0.0.1"))
    port: int = field(default_factory=lambda: int(_env("PORT", "8080")))

    # Fahrzeugbus
    can_interface: str = field(default_factory=lambda: _env("CAN_INTERFACE", "socketcan"))
    can_channel: str = field(default_factory=lambda: _env("CAN_CHANNEL", "can0"))
    # candump-/ASC-Log zum Abspielen statt echtem Bus (auch im sim-Modus nutzbar)
    can_replay: str = field(default_factory=lambda: _env("CAN_REPLAY", ""))
    idrive_map: Path = field(
        default_factory=lambda: Path(_env("IDRIVE_MAP", str(PROJECT_ROOT / "config" / "idrive_map.toml")))
    )

    # Stromversorgung (CarPiHAT): GPIO-Nummern (BCM), siehe Doku des HAT
    ignition_gpio: int = field(default_factory=lambda: int(_env("IGNITION_GPIO", "12")))
    power_latch_gpio: int = field(default_factory=lambda: int(_env("POWER_LATCH_GPIO", "25")))
    shutdown_delay_s: float = field(default_factory=lambda: float(_env("SHUTDOWN_DELAY_S", "30")))

    # Medien
    mpd_host: str = field(default_factory=lambda: _env("MPD_HOST", "localhost"))
    mpd_port: int = field(default_factory=lambda: int(_env("MPD_PORT", "6600")))

    # KI-Agent
    model: str = field(default_factory=lambda: _env("MODEL", "claude-opus-5-5"))
    effort: str = field(default_factory=lambda: _env("EFFORT", "low"))
    # Nach so vielen Sekunden ohne Frage beginnt eine neue Unterhaltung
    agent_idle_reset_s: float = field(default_factory=lambda: float(_env("AGENT_IDLE_RESET_S", "600")))
    web_search: bool = field(default_factory=lambda: _env("WEB_SEARCH", "1") == "1")

    @property
    def is_car(self) -> bool:
        return self.mode == "car"
