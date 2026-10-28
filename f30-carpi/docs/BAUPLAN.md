# Bauplan: Eigenes Infotainment für den BMW F30 320d (2013)

Ziel: Ein Raspberry-Pi-Computer im Auto mit eigener Software (entwickelt mit
Claude Code), Zugriff auf eigene KI-Agenten, Musik und Handyfunktionen
(Telefonie, SMS, Kontakte) – bedient über Touch bzw. den originalen
iDrive-Controller und Sprache.

**Bekannt vom Auto:** **6,5"-Bildschirm (CID, 800×480)**, AUX aktiv, kein
Bluetooth, kein CarPlay. Laut Ausstattungsliste (VIN-Abfrage): **keine
Navigation (kein SA 606/609), kein Bluetooth/USB (kein SA 6NS/6NH/6FL)**,
dafür SA 6VB „Steuerung Infotainment“. → Serienradio **HU-B / ENTRY**
(„Radio Professional“) mit CIC-ähnlichem Menü, **kein CIC**.

**Entscheidung:** Weg A – Bild per Video-Interface auf dem **Original-CID**.

> Preise sind Richtwerte aus Shop-/eBay-Angeboten (Stand Okt. 2026) bzw. als
> „Schätzung“ markiert. Vor dem Kauf prüfen.

---

## 1. Grundprinzip

```
                 ┌──────────────────────────── Auto ──────────────────────────────┐
 Handy ──BT────► │  Raspberry Pi 5 ──HDMI 480p──► Video-Interface ──► Original-CID 6,5" │
 (HFP/A2DP/PBAP) │   │                     (zwischen Radio und CID im LVDS-Kabel)    │
                 │   │  CarPiHAT PRO 5                                              │
                 │   ├─ DAC ──3,5 mm──► AUX-In ──► Radio ──► Lautsprecher           │
 Internet ◄─LTE─ │   ├─ CAN (nur lesen) ◄── K-CAN am iDrive-Controller-Stecker      │
 (Claude-API)    │   ├─ Einschalteingang ◄── Sicherung mit Kl. 15N bzw. 30B         │
                 │   └─ 12 V → 5 V (5 A), sicheres Herunterfahren ◄── Kl. 30        │
                 │  USB-Mikrofon (Dachhimmel) ──► Sprache / Freisprechen          │
                 └────────────────────────────────────────────────────────────────┘
```

- **Das Radio bleibt drin** und dient als Verstärker: Der Pi gibt alles (Musik,
  Telefon, Sprachausgabe) über den vorhandenen **AUX-Eingang** aus.
- **Der Pi liest den Fahrzeugbus nur mit** (iDrive-Controller, Lenkradtasten,
  Klemmenstatus). Er sendet **nichts** auf den Bus.
- **Das Handy** wird per Bluetooth wie bei einer Freisprechanlage gekoppelt:
  Telefonie (HFP), Musik (A2DP/AVRCP), Kontakte (PBAP), SMS (MAP).
- **Internet** für den KI-Agenten über Handy-Hotspot oder LTE-Stick.

## 2. Bildschirm: Original-CID (6,5") mit Video-Interface

Das Interface sitzt zwischen Radio und CID im Videokabel (LVDS) und schaltet
zwischen Originalbild und Pi-Bild (HDMI) um. Ergebnis: werksnahe Optik,
Radio- und Fahrzeugmenüs bleiben, **kein Touch** – die Software wird
ausschließlich per iDrive-Controller, Lenkradtasten und Sprache bedient.

### 2.1 Welches Radio? (geklärt: HU-B / ENTRY)

| Prüfung | HU-B / ENTRY („Radio Professional“) | CIC |
|---|---|---|
| Typschild am Radio (Radio sitzt verdeckt hinter der Bedieneinheit Radio/Klima, nur nach Ausbau sichtbar) | „HU-B“/„Radio Professional“, Teilenr. z. B. 65129262467, 65129270373 | „HU CIC“ |
| **Ausstattungsliste per VIN (am einfachsten, ohne Ausbau)** | SA 663 (Radio Professional), kein SA 609 | meist mit Navigation (SA 609/606) |
| Videostecker (nur nach Ausbau sichtbar, CID-Kabel läuft verdeckt ins Armaturenbrett) | laut Händlern 6-polig LVDS bei ENTRY/NBT | 4-polig HSD-LVDS |

Eine BMW-Servicemitteilung nennt das HU-B ausdrücklich für F30, die **vor
April 2013 ohne Navigation Professional (SA 609)** gebaut wurden; ein Forum
bestätigt, dass ENTRY-Radios im F30 ein CIC-ähnliches Menü zeigen. Der
Videostecker ist das, was beim Interface-Kauf zählt; ohne Ausbau klärt die
Ausstattungsliste per VIN die Radio-Variante.

### 2.2 Interface-Kandidaten

| Interface | passt laut Händler | Eingang | Preis |
|---|---|---|---|
| **Car Solutions „Video Interface with HDMI for BMW with Active Parking Guidelines“** (Favorit) | F30 mit 6,5"-CID; Radios „Entry, EntryNAV, NBT“; laut Listing Bedienung über den iDrive-Controller | HDMI (**nur 480p**), Kameras | ≈ 230 $ (+ Versand/Zoll) |
| NAViKS F30 HDMI-Interface (eBay) | F30 2012–2017 | HDMI, Front-/Rückkamera; Ton über AUX | ≈ 430 $ |
| car-interface.com CI-RL3-CIC-BM | „Business/Professional CIC-E und CIC F-Serie“, 4-Pin-LVDS | AV/RGB | 319 € |

- **Favorit** ist das Car-Solutions-Interface: Es nennt ENTRY und 6,5"
  ausdrücklich und hat HDMI. 480p passt gut zum 800×480-Bildschirm.
- Das car-interface.com-Modul (nur CIC, 4-polig) **passt nicht** – das Auto
  hat kein CIC.
- Vor der Bestellung dem Händler schreiben: Baujahr/VIN und die
  Sonderausstattungs-Codes (SA-Liste) – und fragen, **wie umgeschaltet
  wird** (Taste lang drücken?) und **ob die iDrive-Eingaben im Pi-Modus
  weiter ans Radio gehen** (dann bewegt man „blind“ auch das Radiomenü).

### 2.3 Pi-Ausgabe auf 480p

Das HDMI des Interfaces nimmt nur 480p. Der Pi wird fest auf 720×480
eingestellt (`/boot/firmware/cmdline.txt`, siehe README); die Oberfläche
skaliert sich darauf (getestet für 720×480 und 800×480).

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
| 3 | **Video-Interface mit HDMI für F30 6,5" (ENTRY)**, siehe 2.2 | Pi-Bild auf Original-CID | ≈ 220–400 € inkl. Versand/Zoll (Schätzung) |
| 4 | USB-SSD 128 GB oder High-Endurance-microSD | System | 20–40 € (Schätzung) |
| 5 | USB-Mikrofon mit Echounterdrückung bzw. Mikrofon-Array | Sprache und Freisprechen | 30–60 € (Schätzung) |
| 6 | USB-Bluetooth-5-Stick mit Antenne (optional) | besserer Empfang | 15 € (Schätzung) |
| 7 | LTE-Stick + Daten-SIM (optional) | Internet ohne Hotspot | 0–50 € (Schätzung) |
| 8 | 2× Add-a-Fuse, Kabel, 3,5-mm-Klinke, Y-Adapter/Abzweig für ZBE-Stecker | Strom, Audio, CAN | 30–50 € (Schätzung) |
| 9 | Ggf. Low-Speed-CAN-Transceiver (TJA1055-Modul) | falls K-CAN fehlertolerant ist | 10–20 € (Schätzung) |
| 10 | **Optional:** Carlinkit CPC200-CCPA | CarPlay/Android Auto im eigenen UI | ≈ 70 € |

**Summe Kernsystem: ≈ 520–850 €** (je nach Interface und ob ein Low-Speed-Transceiver nötig ist).

*Verworfen:* eigenes 12,3"-Touch-Display (Weg B) – nur falls kein passendes Interface lieferbar ist.

## 6. Ausbaustufen

| Stufe | Inhalt | Ergebnis |
|---|---|---|
| **0 Schreibtisch** | Software im Simulationsmodus am PC (`CARPI_MODE=sim`) | UI, Agent, Abläufe testen ohne Auto |
| **1 Messen am Auto** | Radio-Typschild + CID-Stecker fotografieren, Sicherungen mit 15N/30B finden, CAN-Pegel am ZBE-Stecker messen | Kaufentscheidung Interface/Transceiver |
| **2 Prüfstand** | Pi + CarPiHAT + Bildschirm an 12-V-Netzteil, Handy koppeln | Musik und Anrufe am Tisch |
| **3 Grundeinbau** | Strom, Bild, AUX-Audio, Mikrofon | Musik, Telefon, Agent im Auto |
| **4 Fahrzeugbus** | CAN listen-only am ZBE-Stecker, `tools/can_sniff.py`: Drehsteller, Tasten, Lenkradtasten, Klemmenstatus → `config/idrive_map.toml` | Bedienung per Original-iDrive |
| **5 Sprache** | Aktivierungswort, Spracherkennung, Sprachausgabe | freihändig |
| **6 Extras** | CarPlay-Dongle, Rückfahrkamera, OBD-Daten | Komfort |

## 7. Risiken und wie wir sie klein halten

- **Fahrzeugbus:** ausschließlich lesen (`listen-only`). Falsches Senden kann
  Fehlermeldungen oder Steuergeräte-Probleme auslösen.
- **iDrive doppelt belegt:** Das Radio empfängt weiterhin alle
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
- Car Solutions HDMI-Interface (Entry/EntryNAV/NBT, 480p): https://car-solutions.com/en/video-interface-with-hdmi-for-bmw-with-active-parking-guidelines/
- NAViKS F30 HDMI-Interface: https://www.ebay.com/itm/251891505551
- car-interface.com CI-RL3-CIC-BM: https://www.car-interface.com/vendita/en/interfaces-a-v-video-bmw/1376-video-interface-for-bmw-businessprofessional-cic-e-and-cic-f-series.html
- BMW-Servicemitteilung HU-B (F30 vor 04/2013 ohne SA 609): https://manuals.autorepairshq.com/BMW/2013/328i%20xDrive%20Sedan%20AWD%20%28F30%29%20L4-2.0L%20Turbo%20%28N26%29/Repair%20and%20Diagnosis/Technical%20Service%20Bulletins/Customer%20Interest/Audio%20Sys%20-%20Headunit-Basic%20Doesn%27t%20Start%20Up%20and%20%27BMW%27%20Displayed
- Forum: ENTRY-Radio mit CIC-ähnlichem Menü: https://f30.bimmerpost.com/forums/showthread.php?t=1065626
- Teilenummern Radio Professional (HU_ENTRY): https://www.go-parts.com/garage/cd-player-bmw-328i-bmw-320i-bmw-335i-2012-2016
- react-carplay: https://github.com/rhysmorgan134/react-carplay
- Pi 5 + BMW-iDrive über CAN (Hudiy-Forum): https://hudiy.eu/community/viewtopic.php?p=1716
- HFP am Pi (Sipfront): https://sipfront.com/blog/2025/03/automating-calls-on-real-mobile-devices-with-bluetooth-hfp-on-a-raspberry-pi/
- BMW Bus-Systeme (Schulungsunterlagen): https://archive.org/download/BMWTechnicalTrainingDocuments/ST811%20F01%20Complete%20Vehicle/03.1_F01%20Bus%20Systems.pdf
