# f30-carpi – eigenes Infotainment für den BMW F30

Raspberry Pi 5 + eigene Software: KI-Assistent (Claude), Musik, Telefon
(Bluetooth), Bedienung per Original-iDrive, Touch und später per Sprache.
Das CIC-Radio bleibt eingebaut und dient als Verstärker (Ton über AUX); das
Bild kommt per Video-Interface auf den Original-Bildschirm oder auf ein
eigenes 12,3"-Display.

- **Hardware, Kosten, Einbau, Risiken:** [`docs/BAUPLAN.md`](docs/BAUPLAN.md)
- **Hinweise für die Weiterentwicklung mit Claude Code:** [`CLAUDE.md`](CLAUDE.md)

## Schnellstart am PC (Simulation)

```bash
cd f30-carpi
python3 -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'
export ANTHROPIC_API_KEY=sk-ant-...   # optional, sonst ist der Assistent aus
python -m carpi                       # http://127.0.0.1:8080
pytest
```

Bedienung im Browser: `←`/`→` = iDrive drehen, `Enter` = drücken,
`Esc` = zurück. Telefon und Musik sind simuliert (Demo-Kontakte, Demo-Titel).

## Einstellungen (Umgebungsvariablen)

| Variable | Standard | Bedeutung |
|---|---|---|
| `CARPI_MODE` | `sim` | `car` = echte Hardware (oFono, MPD, CAN, GPIO) |
| `CARPI_MODEL` | `claude-opus-5-5` | Claude-Modell des Assistenten |
| `CARPI_EFFORT` | `low` | Denkaufwand (`low` = schnelle Antworten beim Fahren) |
| `CARPI_WEB_SEARCH` | `1` | Websuche für den Assistenten |
| `CARPI_AGENT_IDLE_RESET_S` | `600` | Nach so vielen Sekunden Pause neue Unterhaltung |
| `CARPI_CAN_CHANNEL` | `can0` | CAN-Schnittstelle |
| `CARPI_CAN_REPLAY` | – | candump-Log abspielen statt Live-Bus |
| `CARPI_IDRIVE_MAP` | `config/idrive_map.toml` | Zuordnung der CAN-Botschaften |
| `CARPI_IGNITION_GPIO` / `CARPI_POWER_LATCH_GPIO` | `12` / `25` | GPIOs des CarPiHAT (laut HAT-Doku prüfen!); Eingang hängt an Kl. 15N/30B |
| `CARPI_SHUTDOWN_DELAY_S` | `30` | Wartezeit, nachdem Kl. 15N/30B abgefallen ist |
| `CARPI_MPD_HOST` / `CARPI_MPD_PORT` | `localhost` / `6600` | Musik-Daemon |

Der Assistent nutzt server-seitige Fallbacks (`fallbacks: "default"`): Lehnt
das Modell eine Anfrage ab, beantwortet die API sie mit einem Ausweichmodell.

## Einrichtung auf dem Pi (Kurzfassung)

1. Raspberry Pi OS Lite (64 Bit) auf SSD, Benutzer `carpi`.
2. Pakete: `sudo apt install bluez ofono pipewire wireplumber mpd cage chromium can-utils python3-venv`
3. Projekt nach `/opt/f30-carpi`, dann `python3 -m venv .venv && .venv/bin/pip install -e '.[car]'`
4. `/etc/carpi.env` (chmod 600): `CARPI_MODE=car`, `CARPI_HOST=127.0.0.1`, `ANTHROPIC_API_KEY=...`
5. `deploy/carpi.service` nach `/etc/systemd/system/`, aktivieren.
6. `deploy/can0.network` nach `/etc/systemd/network/80-can0.network` (nur mitlesen!).
7. CarPiHAT: Overlays für CAN (MCP2515) und ggf. `gpio-poweroff` laut Hersteller-Doku in `/boot/firmware/config.txt`.
8. PipeWire: HFP-Backend auf `ofono` stellen, Echo-Unterdrückung (`module-echo-cancel`) für das Mikrofon.
9. Handy koppeln: `bluetoothctl` → `pair`, `trust`, `connect`.
10. Kiosk: `deploy/kiosk.sh` beim Login des Benutzers `carpi` starten.

## Stand

| Bereich | Stand |
|---|---|
| Oberfläche (1920×720, Fokus-Bedienung) | funktioniert (Simulation) |
| Claude-Assistent mit Werkzeugen (Anruf, SMS, Musik, Lautstärke, Websuche) | funktioniert, getestet mit Attrappe der API |
| iDrive-/Klemmenstatus-Decoder + Sniff-Werkzeug | fertig, **CAN-IDs am Auto noch zu ermitteln** |
| Layout für Original-CID (800×480 / 1280×480) | funktioniert (Simulation) |
| Telefon über oFono | geschrieben, **noch nicht am Gerät getestet** |
| Musik über MPD | geschrieben, **noch nicht am Gerät getestet** |
| Zündung/Herunterfahren | geschrieben, GPIOs laut CarPiHAT-Doku prüfen |
| Sprache (Aktivierungswort, Spracherkennung, Sprachausgabe) | offen (Stufe 4) |
| Telefonbuch per PBAP, SMS-Empfang per MAP | offen |
| CarPlay/Android Auto über Carlinkit-Dongle | offen (optional) |
