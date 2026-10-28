# Bauplan: Eigenes Infotainment für den BMW F30 320d (2013)

Ziel: Ein Raspberry-Pi-Computer im Auto mit eigener Software (entwickelt mit
Claude Code), Zugriff auf eigene KI-Agenten, Musik und Handyfunktionen
(Telefonie, SMS, Kontakte) – bedient über Touch bzw. den originalen
iDrive-Controller und Sprache.

**Bekannt vom Auto:** Radio = **CIC**, **AUX-Eingang vorhanden**, kein
Bluetooth, kein CarPlay.

> Preise sind Richtwerte aus Shop-/eBay-Angeboten (Stand Okt. 2026) bzw. als
> „Schätzung“ markiert. Vor dem Kauf prüfen.

---

## 1. Grundprinzip

```
                 ┌──────────────────────────── Auto ──────────────────────────────┐
 Handy ──BT────► │  Raspberry Pi 5 ──HDMI──► Bild: (A) Video-Interface → Original-CID │
 (HFP/A2DP/PBAP) │   │                             oder (B) eigenes 12,3"-Display     │
                 │   │  CarPiHAT PRO 5                                              │
                 │   ├─ DAC ──3,5 mm──► AUX-In ──► CIC-Radio ──► Lautsprecher       │
 Internet ◄─LTE─ │   ├─ CAN (nur lesen) ◄── K-CAN am iDrive-Controller-Stecker      │
 (Claude-API)    │   ├─ Einschalteingang ◄── Sicherung mit Kl. 15N bzw. 30B         │
                 │   └─ 12 V → 5 V (5 A), sicheres Herunterfahren ◄── Kl. 30        │
                 │  USB-Mikrofon (Dachhimmel) ──► Sprache / Freisprechen          │
                 └────────────────────────────────────────────────────────────────┘
```

- **Das CIC bleibt drin** und dient als Verstärker: Der Pi gibt alles (Musik,
  Telefon, Sprachausgabe) über den vorhandenen **AUX-Eingang** aus.
- **Der Pi liest den Fahrzeugbus nur mit** (iDrive-Controller, Lenkradtasten,
  Klemmenstatus). Er sendet **nichts** auf den Bus.
- **Das Handy** wird per Bluetooth wie bei einer Freisprechanlage gekoppelt:
  Telefonie (HFP), Musik (A2DP/AVRCP), Kontakte (PBAP), SMS (MAP).
- **Internet** für den KI-Agenten über Handy-Hotspot oder LTE-Stick.

## 2. Bildschirm: zwei Wege

Weil ein **CIC** verbaut ist, gibt es fertige Video-Interfaces, die ein
fremdes Bild in den **Original-Bildschirm (CID)** einspeisen. Das war beim
vermuteten Basisradio unklar.

| | **(A) Original-CID + Video-Interface** | **(B) Eigenes 12,3"-Display** |
|---|---|---|
| Optik | original, nichts sichtbar verändert | Nachrüst-Optik, 3D-gedruckter Halter |
| Auflösung | 800×480 (6,5") bzw. 1280×480 (8,8") | 1920×720 |
| Touch | nein → Bedienung nur per iDrive und Sprache | ja |
| CIC-Menüs (Radio, Fahrzeugeinstellungen) | bleiben, Umschalten per Taste | entfallen (CID wird ersetzt) |
| Kosten | Interface ≈ 250–400 € | Display ≈ 160 € + Halter |
| Aufwand | Stecker zwischen CIC und CID (LVDS) | Halter bauen, CID ausbauen |

**Empfehlung: (A)**, solange ein passendes Interface für deinen Bildschirm
gefunden wird – es ist werksnah, die Fahrzeugeinstellungen bleiben, und
iDrive-Bedienung plus Sprache passen ohnehin zum Konzept. Die Oberfläche der
Software passt sich an 800×480, 1280×480 und 1920×720 an.

Vorher prüfen:
- **Bildschirmgröße** (6,5" oder 8,8"). Laut Händlerlisten hatten F30 mit CIC
  meist 8,8" (1280×480), es gibt aber auch 6,5" (800×480).
- **Eingänge des Interfaces:** Viele CIC-Interfaces haben nur RGB/Composite
  (FBAS) als Eingang, manche HDMI. Für den Pi ist **HDMI** ideal; sonst
  braucht es einen HDMI→Composite-Wandler (schlechteres Bild) – oder den
  Composite-Ausgang des Pi.
- **Stecker:** F-Serie-CIDs hängen per 4-poligem HSD-LVDS-Stecker am Radio
  (z. B. Ampire V5-CIC-F-PNP: „F-series with navigation system or radio and
  7", 8.8" or 10.2" monitor with 4-pin HSD LVDS“ – 6,5" vorab beim Händler
  erfragen).

## 3. Strom: Klemme 15 gibt es im F30 nur virtuell

Im F30 gibt es kein klassisches, vom Zündschlüssel geschaltetes Zündungsplus
mehr; Klemme 15 ist ein Status auf dem Fahrzeugbus. Als Kabel gibt es
geschaltete Klemmen wie **15N** (Nachlauf: bleibt nach dem Ausschalten noch
eine Weile an) und **30B** (an, solange das Fahrzeug „wach“ ist). Auch die
12-V-Steckdosen laufen nach.

Für den Pi ist das sogar praktisch:

- **Einschalteingang des CarPiHAT an eine Sicherung mit 15N** (Add-a-Fuse im
  Sicherungskasten). Der Pi startet mit der Zündung, bleibt beim kurzen
  Halt an, und fährt herunter, wenn 15N abfällt.
- **Alternative 30B:** Der Pi bootet schon beim **Aufschließen** und ist
  beim Losfahren fertig (Bootzeit des Pi ≈ 20–30 s). Kostet etwas mehr
  Batterie, wenn das Auto lange „wach“ steht.
- **Welche Sicherung welche Klemme führt:** am eigenen Auto mit dem
  Multimeter prüfen (Zündung aus / an / verriegelt / nach 1, 5, 15 min) –
  nicht nach Tabellen aus dem Internet.
- **Den genauen Zündungszustand** liest die Software zusätzlich vom Bus
  (Klemmenstatus-Botschaft, mit `tools/can_sniff.py` ermitteln und als
  `[ignition]` in `config/idrive_map.toml` eintragen).
- **Dauerplus (Kl. 30)** für den CarPiHAT, eigene Sicherung (5 A).

## 4. Fahrzeugbus am iDrive-Controller abgreifen

Der Stecker direkt unter dem iDrive-Controller (ZBE) führt den K-CAN – dort
greifen auch fertige CarPlay-Boxen und Android-Displays ab. Das ist der
bequemste Punkt (Mittelkonsole, kurze Wege).

**Vor dem Anschließen messen** (Zündung an, Multimeter gegen Masse):

| Messung | High-Speed-CAN | Low-Speed-/Fehlertolerant-CAN |
|---|---|---|
| CAN-H in Ruhe | ≈ 2,5 V | ≈ 0 V |
| CAN-L in Ruhe | ≈ 2,5 V | ≈ 5 V |

- Der CAN-Baustein des CarPiHAT ist ein **High-Speed**-Transceiver. Zeigt die
  Messung „fehlertolerant“ (typisch für ältere BMW-K-CAN mit 100 kbit/s),
  braucht man stattdessen einen Low-Speed-Transceiver (z. B. TJA1055) – vor
  dem Kauf klären! Für den F30 habe ich dazu keine verlässliche Quelle
  gefunden; Quellen nennen für K-CAN teils 100, teils 500 kbit/s.
- Kabelfarben aus Foren/KI-Antworten (z. B. „Grün und Orange/Grün“) nur als
  Hinweis nehmen; maßgeblich sind Schaltplan und Messung.
- **Abgreifen ohne Schneiden:** Y-Kabel/Adapter für den ZBE-Stecker (wie bei
  CarPlay-Boxen) oder Stromdieb-freie Abzweigung mit Lötverbindern.
- Bitrate in `deploy/can0.network` anpassen; falsche Bitrate im
  Listen-only-Modus stört den Bus nicht, man sieht nur keine Daten.

## 5. Teileliste

| # | Teil | Zweck | ca. Preis |
|---|---|---|---|
| 1 | Raspberry Pi 5, 8 GB + Active Cooler | Rechner | 95–110 € (Schätzung) |
| 2 | **CarPiHAT PRO 5** | 12 V→5 V/5 A, Sicherung + Filter, Einschalteingang, sicheres Herunterfahren, CAN, Audio-DAC, < 1 mA Ruhestrom | ≈ 100–130 € (£88–110) |
| 3a | **Video-Interface für F-Serie-CIC** mit HDMI- oder AV-Eingang (Weg A) | Pi-Bild auf Original-CID | ≈ 250–400 € |
| 3b | *oder* 12,3" HDMI-Touch 1920×720 + Halter (Weg B) | eigener Bildschirm | ≈ 170–190 € |
| 4 | USB-SSD 128 GB oder High-Endurance-microSD | System | 20–40 € (Schätzung) |
| 5 | USB-Mikrofon mit Echounterdrückung bzw. Mikrofon-Array | Sprache und Freisprechen | 30–60 € (Schätzung) |
| 6 | USB-Bluetooth-5-Stick mit Antenne (optional) | besserer Empfang | 15 € (Schätzung) |
| 7 | LTE-Stick + Daten-SIM (optional) | Internet ohne Hotspot | 0–50 € (Schätzung) |
| 8 | 2× Add-a-Fuse, Kabel, 3,5-mm-Klinke, Y-Adapter/Abzweig für ZBE-Stecker | Strom, Audio, CAN | 30–50 € (Schätzung) |
| 9 | Ggf. Low-Speed-CAN-Transceiver (TJA1055-Modul) | falls K-CAN fehlertolerant ist | 10–20 € (Schätzung) |
| 10 | **Optional:** Carlinkit CPC200-CCPA | CarPlay/Android Auto im eigenen UI | ≈ 70 € |

**Summe Kernsystem:** Weg A ≈ **550–850 €**, Weg B ≈ **470–640 €**.

## 6. Ausbaustufen

| Stufe | Inhalt | Ergebnis |
|---|---|---|
| **0 Schreibtisch** | Software im Simulationsmodus am PC (`CARPI_MODE=sim`) | UI, Agent, Abläufe testen ohne Auto |
| **1 Messen am Auto** | CID-Größe ablesen, Sicherungen mit 15N/30B finden, CAN-Pegel am ZBE-Stecker messen | Kaufentscheidung Interface/Transceiver |
| **2 Prüfstand** | Pi + CarPiHAT + Bildschirm an 12-V-Netzteil, Handy koppeln | Musik und Anrufe am Tisch |
| **3 Grundeinbau** | Strom, Bild, AUX-Audio, Mikrofon | Musik, Telefon, Agent im Auto |
| **4 Fahrzeugbus** | CAN listen-only am ZBE-Stecker, `tools/can_sniff.py`: Drehsteller, Tasten, Lenkradtasten, Klemmenstatus → `config/idrive_map.toml` | Bedienung per Original-iDrive |
| **5 Sprache** | Aktivierungswort, Spracherkennung, Sprachausgabe | freihändig |
| **6 Extras** | CarPlay-Dongle, Rückfahrkamera, OBD-Daten | Komfort |

## 7. Risiken und wie wir sie klein halten

- **Fahrzeugbus:** ausschließlich lesen (`listen-only`). Falsches Senden kann
  Fehlermeldungen oder Steuergeräte-Probleme auslösen.
- **iDrive doppelt belegt:** Bei Weg A empfängt auch das CIC weiter alle
  Dreh-/Drückbefehle. Die Software sollte nur reagieren, wenn ihr Bild
  gerade angezeigt wird (Umschaltlogik des Interfaces beachten).
- **Batterie:** Pi muss sauber herunterfahren und dann stromlos sein
  (CarPiHAT: < 1 mA). Nicht ungeschaltet an Dauerplus betreiben.
- **Hitze:** aktiver Kühler; Software drosselt sich bei Überhitzung.
- **Stromausfälle:** SSD statt billiger SD-Karte, Dateisystem möglichst
  read-only/overlay.
- **Airbag-Bereiche:** nichts im Auslösebereich montieren.
- **Ablenkung (StVO § 23):** große Bedienelemente, iDrive und Sprache,
  komplexe Eingaben nur im Stand.
- **Zulassung/Versicherung:** keine Rechtsberatung – im Zweifel vorher bei
  TÜV/DEKRA nachfragen.

## 8. Software (dieses Repository)

Siehe `README.md` und `CLAUDE.md`.

## Quellen

- CarPiHAT PRO 5: https://thepihut.com/products/carpihat-pro-5-car-interface-dac-for-raspberry-pi-5
- Ampire V5-CIC-F-PNP (Handbuch): https://pdf.ampire.de/caraudiosystems/V5-CIC-F-PNP/man_eng_V5-CIC-F-PNP.pdf
- Video-Interface BMW CIC (Audiovisualworld): https://audiovisualworld.co.uk/bmw-idrive-cic-multimedia-video-interface-with-digital-radio-digital-tv-control-and-pip-sku572.html
- NavInc Interface CIC: https://www.navinc.nl/multimedia-video-interface-bmw-idrive-cic-cic2-systems-3780
- Nickl Fahrzeugliste (CID-Größen/Auflösungen F30): https://nickl.de/en/Products/CarImaging/VehicleList/
- 12,3" HDMI 1920×720: https://spotpear.com/shop/Raspberry-Pi-12.3-inch-HDMI-LCD-Captive-TouchScreen-Display-1920x720.html
- react-carplay: https://github.com/rhysmorgan134/react-carplay
- Pi 5 + BMW-iDrive über CAN (Hudiy-Forum): https://hudiy.eu/community/viewtopic.php?p=1716
- HFP am Pi (Sipfront): https://sipfront.com/blog/2025/03/automating-calls-on-real-mobile-devices-with-bluetooth-hfp-on-a-raspberry-pi/
- BMW Bus-Systeme (Schulungsunterlagen): https://archive.org/download/BMWTechnicalTrainingDocuments/ST811%20F01%20Complete%20Vehicle/03.1_F01%20Bus%20Systems.pdf
