# CLAUDE.md – f30-carpi

Eigenes Infotainment für einen BMW F30 320d (2013, Basisradio HU_ENTRY mit
6,5"-CID, ohne Bluetooth/Navi). Hardware: Raspberry Pi 5 + CarPiHAT PRO 5 +
12,3"-HDMI-Touch (1920×720). Details: `docs/BAUPLAN.md`.

## Architektur

- `carpi/events.py` – Ereignisbus; alle Module tauschen dicts mit `"type"` aus.
- `carpi/server.py` – FastAPI; liefert `carpi/ui/` aus und koppelt UI und Bus per `/ws`.
- `carpi/vehicle/` – CAN (python-can, nur Empfang), iDrive-Decoder (`idrive.py`), Zündung/Herunterfahren (`power.py`).
- `carpi/phone/` – Protokoll `PhoneService`; `SimulatedPhone` (PC), `OfonoPhone` (Pi, D-Bus).
- `carpi/media/` – Protokoll `MediaService`; `SimulatedMedia`, `MpdMedia`.
- `carpi/agent/` – Claude-Agent (`claude_agent.py`, eigener Tool-Loop) und Werkzeuge (`tools.py`).
- `carpi/ui/` – Vanilla HTML/CSS/JS, kein Build-Schritt. Bedienung per Fokus (Drehsteller).
- `CARPI_MODE=sim` (Standard) läuft ohne Auto-Hardware; `car` nutzt echte Dienste.

## Regeln

- **Niemals auf den Fahrzeug-CAN senden.** Die Schnittstelle läuft listen-only; `can_source.py` hat bewusst keine Sendefunktion. Änderungen daran nur nach ausdrücklicher Rücksprache.
- CAN-IDs gehören in `config/idrive_map.toml`, nicht in den Code. Nicht erfinden: nur am Auto ermittelte Werte eintragen.
- Claude-API: offizielles `anthropic`-SDK, Modell aus `Settings.model` (Standard `claude-opus-5-5`), `thinking: adaptive`, Effort aus Settings, `fallbacks: "default"` mit Beta `server-side-fallback-2026-07-01`. Konversation nur anhängen, nie nachträglich bearbeiten (stattdessen `reset()`).
- Neue Agent-Werkzeuge: Definition in `TOOL_DEFINITIONS` (strict, `additionalProperties: false`) + Methode `tool_<name>` in `Toolbox` + Test in `tests/test_agent.py`.
- UI-Texte auf Deutsch, große Schrift, alles muss per Drehsteller (Fokus) erreichbar sein.
- Hardwarenahe Bibliotheken (dbus-fast, python-mpd2, gpiozero) nur lazy importieren, damit `sim` auf jedem PC läuft.

## Befehle

```bash
pip install -e '.[dev]'
pytest                 # alle Tests (ohne Hardware, ohne API-Schlüssel)
python -m carpi        # Server auf http://127.0.0.1:8080
python tools/can_sniff.py --channel can0   # am Auto: iDrive-Botschaften finden
```

## Nächste Schritte (Roadmap)

1. Prüfstand: oFono/MPD am echten Pi testen, Fehler beheben.
2. Am Auto: K-CAN-Bitrate und iDrive-/Lenkrad-IDs ermitteln → `idrive_map.toml`.
3. Sprache: Aktivierungswort (z. B. openWakeWord), Spracherkennung (lokal whisper.cpp oder Cloud), Sprachausgabe (z. B. Piper) – als eigener Dienst, der `agent.ask` aufruft.
4. Telefonbuch per PBAP (obexd), eingehende SMS per MAP, eingehende Anrufe als Ereignis `phone.call`/`incoming` aus oFono-Signalen.
5. Optional: CarPlay/Android Auto über Carlinkit CPC200-CCPA, Rückfahrkamera, OBD-Daten.
