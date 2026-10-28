# Bauplan: Eigenes Infotainment für den BMW F30 320d (2013, Grundausstattung)

Ziel: Ein Raspberry-Pi-Computer mit eigenem Display im Auto, eigener Software
(entwickelt mit Claude Code), Zugriff auf eigene KI-Agenten, Musik und
Handyfunktionen (Telefonie, SMS, Kontakte) – bedient über Touch, den
originalen iDrive-Controller und Sprache.

> Preise sind Richtwerte aus Shop-/eBay-Angeboten (Stand Okt. 2026) bzw. als
> „Schätzung“ markiert. Vor dem Kauf prüfen.

---

## 1. Grundprinzip

```
                 ┌──────────────────────────── Auto ───────────────────────────┐
 Handy ──BT────► │  Raspberry Pi 5  ──HDMI+USB-Touch──► 12,3" Display (1920x720)│
 (HFP/A2DP/PBAP) │   │  CarPiHAT PRO 5                                          │
                 │   ├─ DAC ──3,5 mm──► AUX-In ──► Original-Radio (HU) ─► Boxen │
 Internet ◄─LTE─ │   ├─ CAN (nur lesen) ◄── K-CAN ◄── iDrive-Controller, Lenkrad│
 (Claude-API)    │   ├─ Zündungseingang ◄── Kl. 15 / ACC                        │
                 │   └─ 12 V → 5 V (5 A), sicheres Herunterfahren ◄── Kl. 30    │
                 │  USB-Mikrofon (Dachhimmel) ──► Sprache / Freisprechen       │
                 └─────────────────────────────────────────────────────────────┘
```

- **Das Original-Radio bleibt drin** und dient als Verstärker: Der Pi gibt
  alles (Musik, Telefon, Sprachausgabe) über den **AUX-Eingang** aus.
- **Der Pi liest den Fahrzeugbus nur mit** (iDrive-Dreh-Drück-Steller,
  Lenkradtasten). Er sendet anfangs **nichts** auf den Bus.
- **Das Handy** wird per Bluetooth wie bei einer Freisprechanlage gekoppelt:
  Telefonie (HFP), Musik (A2DP/AVRCP), Kontakte (PBAP), SMS (MAP).
- **Internet** für den KI-Agenten über Handy-Hotspot oder LTE-Stick.

## 2. Teileliste

| # | Teil | Zweck | ca. Preis |
|---|---|---|---|
| 1 | Raspberry Pi 5, 8 GB + Active Cooler | Rechner | 95–110 € (Schätzung) |
| 2 | **CarPiHAT PRO 5** | 12 V→5 V/5 A, Sicherung + Filter, Zündungs-/Rückwärtsgang-/Licht-Eingänge, CAN, Audio-DAC, sicheres Herunterfahren, < 1 mA Ruhestrom | ≈ 100–130 € (£88–110) |
| 3 | 12,3" HDMI-Touch-Display 1920×720 (z. B. SpotPear) | Bildschirm statt des 6,5"-CID | ≈ 160 € ($168) |
| 4 | USB-SSD 128 GB oder High-Endurance-microSD | System (verträgt Stromausfälle besser) | 20–40 € (Schätzung) |
| 5 | USB-Mikrofon mit Echounterdrückung bzw. Mikrofon-Array | Sprache und Freisprechen | 30–60 € (Schätzung) |
| 6 | USB-Bluetooth-5-Stick mit Antenne (optional) | besserer Empfang als das Onboard-BT | 15 € (Schätzung) |
| 7 | LTE-Stick + Daten-SIM (optional) | Internet ohne Handy-Hotspot | 0–50 € (Schätzung) |
| 8 | Add-a-Fuse/Sicherungsabgriff, Kabel, Stecker, 3,5-mm-Klinke | Stromversorgung, Audio | 20–30 € (Schätzung) |
| 9 | 3D-gedruckter Halter für die CID-Aufnahme | Display-Montage | 10–30 € (Schätzung) |
| 10 | **Optional:** Carlinkit CPC200-CCPA | CarPlay/Android Auto im eigenen UI (Projekte: react-carplay, LIVI, FastCarPlay) | ≈ 70 € |
| 11 | **Optional:** USB-GPS, Rückfahrkamera, OBD-Adapter | Navigation, Kamera, Motordaten | 15–60 € je Teil |

**Summe Kernsystem (1–9): ca. 450–620 €**, mit optionalen Teilen bis ca. 750 €.

### Warum diese Teile

- **CarPiHAT PRO 5:** Eine einzige Platine deckt die schwierigen
  Auto-Themen ab: Spannungsspitzen, Abschalten bei Zündung aus, CAN und
  Audio. Ohne sie bräuchte man Optokoppler, Relais, einen Abwärtswandler
  und eine eigene CAN-Platine.
- **12,3"-HDMI-Display:** direkt am Pi, kein LVDS-Gebastel. Ein
  10,25"-HDMI-Panel mit 1920×720 habe ich nicht gefunden; 10,25"-Autopanels
  gibt es nur mit LVDS (bräuchte LVDS↔HDMI-Wandler).
- **Original-6,5"-Bildschirm weiterverwenden** ist möglich, aber schwierig:
  Er wird vom Radio angesteuert (LVDS bzw. APIX), Video-Einspeiser gibt es
  vor allem für CIC/NBT, für das Basisradio ist das unklar. Das heben wir
  uns als späte Ausbaustufe auf.

## 3. Was am Auto vorher zu klären ist

1. **Radio-Typ:** Typenschild/Teilenummer des Radios oder Ausstattungsliste
   per VIN. Erwartet: „HU_ENTRY“/„Radio Professional“ mit 6,5"-CID.
2. **AUX-Eingang vorhanden?** (Mittelkonsole/Armlehne; im Menü
   *Multimedia → Externe Geräte → AUX*). Falls nicht: per Codierung aktivieren
   oder freischalten lassen.
3. **Wo greifen wir K-CAN ab?** Am Quadlock-Stecker des Radios oder am
   Stecker des iDrive-Controllers. Pinbelegung aus dem Schaltplan (ISTA/
   Schaltplan-Datenbank) – **vor dem Anschließen mit dem Multimeter prüfen**.
   Bitrate ermitteln (K-CAN klassisch 100 kbit/s; neuere K-CAN-Zweige 500 kbit/s).
4. **Zündungsplus (Kl. 15) und Dauerplus (Kl. 30)** für den CarPiHAT, jeweils
   abgesichert.

## 4. Ausbaustufen

| Stufe | Inhalt | Ergebnis |
|---|---|---|
| **0 Schreibtisch** | Software im Simulationsmodus am PC entwickeln (`CARPI_MODE=sim`) | UI, Agent, Abläufe testen ohne Auto |
| **1 Prüfstand** | Pi + CarPiHAT + Display an 12-V-Netzteil, Bluetooth mit Handy koppeln | Musik und Anrufe über Lautsprecher am Tisch |
| **2 Grundeinbau** | Strom, Display, AUX-Audio, Mikrofon ins Auto | Musik, Telefon, Agent per Touch im Auto |
| **3 Fahrzeugbus** | CAN im **Listen-only**-Modus anschließen, mit `tools/can_sniff.py` die Botschaften von iDrive und Lenkradtasten ermitteln, in `config/idrive_map.toml` eintragen | Bedienung über den Original-iDrive-Controller |
| **4 Sprache** | Aktivierungswort, Spracherkennung und Sprachausgabe (lokal oder Cloud) | freihändige Bedienung des Agenten |
| **5 Extras** | CarPlay-Dongle, Rückfahrkamera (Rückwärtsgang-Eingang), Navigation, OBD-Daten, evtl. Original-CID per Video-Einspeisung | Komfort |

## 5. Risiken und wie wir sie klein halten

- **Fahrzeugbus:** Anfangs ausschließlich lesen (`listen-only`). Falsches
  Senden kann Fehlermeldungen oder Steuergeräte-Probleme auslösen.
- **Batterie:** Der Pi muss bei Zündung aus sauber herunterfahren und dann
  stromlos sein (CarPiHAT: < 1 mA). Nie direkt an Dauerplus ohne Abschaltung.
- **Hitze:** Im Sommer kann es hinter dem Armaturenbrett sehr heiß werden.
  Aktiver Kühler, Software drosselt sich bei Überhitzung.
- **Stromausfälle/Kaltstart:** SSD statt billiger SD-Karte, Dateisystem
  möglichst read-only/overlay.
- **Airbag-Bereiche:** Display und Kabel nicht im Auslösebereich der Airbags
  montieren.
- **Ablenkung (StVO § 23):** Das UI ist auf große Bedienelemente, iDrive und
  Sprache ausgelegt. Komplexe Eingaben nur im Stand.
- **Zulassung/Versicherung:** Ein fest eingebautes Zusatzdisplay ist meist
  unkritisch, das ist aber **keine Rechtsberatung**. Im Zweifel vorher bei
  TÜV/DEKRA nachfragen.

## 6. Software (dieses Repository)

Siehe `README.md` und `CLAUDE.md`. Kurz:

- **Backend (Python, asyncio, FastAPI):** Ereignisbus, CAN/iDrive-Decoder,
  Telefon (oFono/BlueZ über D-Bus), Medien (MPD), Claude-Agent mit Werkzeugen.
- **Oberfläche:** Web-UI im Chromium-Kiosk, auf 1920×720 und Bedienung per
  Dreh-Drück-Steller ausgelegt.
- **Simulationsmodus:** läuft auf jedem PC, iDrive per Pfeiltasten.

## Quellen

- CarPiHAT PRO 5: https://thepihut.com/products/carpihat-pro-5-car-interface-dac-for-raspberry-pi-5
- 12,3" HDMI 1920×720: https://spotpear.com/shop/Raspberry-Pi-12.3-inch-HDMI-LCD-Captive-TouchScreen-Display-1920x720.html
- react-carplay (Carlinkit am Pi): https://github.com/rhysmorgan134/react-carplay
- Pi 5 + BMW-iDrive über CAN (Hudiy-Forum): https://hudiy.eu/community/viewtopic.php?p=1716
- HFP am Pi mit PipeWire/oFono: https://sipfront.com/blog/2025/03/automating-calls-on-real-mobile-devices-with-bluetooth-hfp-on-a-raspberry-pi/
- BMW-Servicemitteilung F30 Headunit-Basic/CID: https://static.nhtsa.gov/odi/tsbs/2013/MC-10149314-9999.pdf
- K-CAN-Überblick (opendbc BMW): https://dzid26.github.io/opendbc-BMW-E8x-E9x
