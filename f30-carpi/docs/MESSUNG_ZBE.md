# Messanleitung: Fahrzeugbus am iDrive-Controller (ZBE) – BMW F30

Ziel: herausfinden, **welche Art CAN-Bus** am Stecker des iDrive-Controllers
anliegt. Davon hängt ab, ob der CarPiHAT den Bus direkt lesen kann
(High-Speed-CAN) oder ob ein Low-Speed-/fehlertoleranter Baustein
(TJA1055) nötig ist. Nebenbei messen wir **Klemme 30B** – ein Kandidat für
das Einschaltsignal des Pi.

Dauer: ca. 45–60 Minuten. Es wird **nichts abgesteckt, geschnitten oder
angestochen** – gemessen wird von hinten am eingesteckten Stecker.

> Die Pinbelegung unten stammt aus Foren (nicht aus BMW-Unterlagen). Deshalb
> wird jeder Pin zuerst per Messung bestätigt, bevor etwas daraus folgt.

---

## 1. Werkzeug

| Werkzeug | Wozu |
|---|---|
| Digital-Multimeter (Gleichspannung 20 V, Widerstand) | Messen |
| **Rückseiten-Prüfspitzen** („Backprobe Pins“, dünne Nadeln, ca. 10 €) oder sehr dünne Nähnadeln mit Krokoklemme | von hinten in den Stecker, ohne Kontakte aufzubiegen |
| Kunststoff-Hebelwerkzeuge (Trim-Tool-Set) | Blende lösen, ohne Kratzer |
| Torx-Satz (kleine Größen) | falls der Controller verschraubt ist |
| Taschenlampe/Stirnlampe, Handy für Fotos | Stecker und Kabelfarben dokumentieren |
| Malerkrepp + Stift | Adern beschriften |

**Nicht benutzen:** Prüflampen (ziehen zu viel Strom), Stromdiebe/Abzweig-
verbinder, Messspitzen, die die Isolierung durchstechen.

## 2. Sicherheit und Vorsichtsmaßnahmen

- **Kurzschlüsse vermeiden:** Ein Pin führt 12 V (Kl. 30B, abgesichert).
  Nie zwei Spitzen gleichzeitig an benachbarte Pins halten, wenn sie sich
  berühren könnten. Krokoklemme an Masse, dann nur eine Spitze bewegen.
- **Widerstand nur am stromlosen Bus messen** (siehe Messung D) – nie bei
  wachem Fahrzeug.
- **Kontakte nicht aufweiten:** Prüfspitze an der Ader entlang von hinten in
  die Steckerkammer schieben, nur bis Metallkontakt; nicht in die
  Steckseite stechen.
- Wird der Stecker doch einmal bei wachem Auto gezogen, kann eine Meldung
  oder ein Fehlereintrag entstehen – harmlos, lässt sich später löschen.
- Auto steht sicher (P bzw. Gang + Handbremse), Schlüssel im Auto, Fenster
  einen Spalt offen (falls etwas verriegelt).

## 3. An den Stecker kommen

1. **Fotos machen** von der Mittelkonsole, bevor du etwas löst.
2. Die **Blende um den iDrive-Controller** (mit den Tasten MENU, RADIO usw.)
   ist beim F30 nur **geclipst, nicht verschraubt**. Hebelwerkzeug seitlich
   unter die Kante, gleichmäßig und kräftig nach oben ziehen – rundum
   lösen, nicht nur an einer Ecke.
3. Blende samt Controller vorsichtig anheben – **das Kabel hängt noch
   dran**. Nur so weit hochheben, dass der Stecker an der Unterseite des
   Controllers sichtbar und von hinten erreichbar ist.
4. Kommst du nicht an den Stecker: Laut Forenberichten ist der Controller
   mit einigen kleinen Torx-Schrauben in der Blende befestigt. Erst lösen,
   wenn es nötig ist.
5. **Stecker fotografieren** (Adernfarben, Pinnummern auf dem Gehäuse – oft
   winzig eingeprägt, Taschenlampe schräg halten).

## 4. Was am Stecker zu erwarten ist

Laut Forum hat der Controller-Stecker 4 Pins:

| Pin | Funktion (laut Forum) | typische Farbe (nur Hinweis!) |
|---|---|---|
| 1 | Plus, Klemme 30B | rot/… |
| 2 | Masse | braun (BMW-Masse ist braun) |
| 3 | K-CAN High | z. B. grün **oder** gelb/rot |
| 4 | K-CAN Low | z. B. orange/grün **oder** gelb/braun |

- **Grün + orange/grün** wird in Foren dem „K-CAN 1“ zugeordnet (Fahrzeuge
  mit Radio wie deinem), **gelb/rot + gelb/braun** dem „K-CAN 2“ (NBT).
- Trag in die Tabelle unten ein, welche Farbe auf welchem Pin sitzt.

## 5. Messungen

Multimeter auf **Gleichspannung (V⎓), Bereich 20 V**.
Schwarze Leitung mit Krokoklemme an **Masse**: am besten an Pin 2 (braun)
von hinten, alternativ an eine blanke Masseschraube der Karosserie.

Zustände des Autos:
- **„Zündung an“:** Start-Stopp-Knopf drücken, **ohne** Bremse/Kupplung –
  Motor bleibt aus, Kombiinstrument an.
- **„Schlafend“:** Auto abgeschlossen, 30–60 Minuten nicht berührt.

### Messung A – Plus (Pin 1) bestätigen
1. Zündung an. Rote Spitze an Pin 1.
2. Erwartet: **ca. 12–12,8 V**. Dann ist Pin 1 Plus und Pin 2 Masse
   bestätigt.
3. Zeigt Pin 1 nichts, nacheinander die anderen Pins prüfen; der Pin mit
   ca. 12 V ist Plus. Tabelle anpassen.

### Messung B – CAN-Leitungen gegen Masse
1. Zündung an, nichts bedienen.
2. Rote Spitze an Pin 3, Wert notieren (**CAN-H**).
3. Rote Spitze an Pin 4, Wert notieren (**CAN-L**).
4. Wiederholen, während jemand den **Controller dreht/drückt** – die Werte
   dürfen etwas zappeln (das Multimeter zeigt einen Mittelwert).

### Messung C – zwischen den CAN-Leitungen
1. Zündung an. Schwarze Spitze an Pin 4 (CAN-L), rote an Pin 3 (CAN-H).
2. Wert notieren (kann negativ sein – Vorzeichen mit aufschreiben).

### Messung D (optional) – Widerstand am schlafenden Bus
Nur wenn das Auto **schläft** (Messung E zeigt Pin 1 = 0 V):
1. Multimeter auf **Ω**. Spitzen an Pin 3 und Pin 4.
2. Notieren. Bei High-Speed-CAN typisch **ca. 60 Ω** (zwei
   120-Ω-Abschlüsse parallel).

### Messung E – Wann schaltet Klemme 30B ab? (für die Stromversorgung des Pi)
1. Rote Spitze an Pin 1 lassen (Krokoklemme oder Spitze fixieren), Kabel so
   legen, dass Tür und Blende schließen können – oder Werte durchs Fenster
   ablesen.
2. Notieren: Zündung an → Zündung aus → Tür auf/zu → abgeschlossen → nach
   1, 5, 15, 30 Minuten.
3. Daraus sehen wir, ob 30B als Einschaltsignal für den Pi taugt.
   **Nur als Signal** – keinen Strom für den Pi von diesem Pin abzweigen.

## 6. Auswertung

| Ergebnis (Zündung an) | Bedeutung | Folge |
|---|---|---|
| CAN-H ≈ 2,5–3,0 V, CAN-L ≈ 2,0–2,5 V, Differenz H−L ≈ 0–0,5 V | **High-Speed-CAN** | CarPiHAT liest direkt. Bitrate später mit dem Sniff-Werkzeug finden (erst 100 kbit/s, dann 500 kbit/s – alles listen-only). |
| CAN-H ≈ 0,2–1 V, CAN-L ≈ 4–4,8 V, Differenz H−L ≈ −3 bis −4,5 V | **Low-Speed-/fehlertolerantes CAN** | Zusätzlicher Baustein mit **TJA1055** nötig (ca. 10–20 €); Software bleibt gleich. |
| Alle Pins ≈ 0 V | Bus schläft oder falsche Pins | Zündung wirklich an? Pins neu zuordnen. |
| Werte anders als oben | unklar | Fotos + Werte schicken, nicht weiter anschließen. |

Die Werte für fehlertolerantes CAN stammen aus Foren zu älteren BMW
(K-CAN ca. 0,2 V / 4,8 V in Ruhe); die High-Speed-Werte sind die üblichen
Normwerte. Ein Multimeter zeigt bei laufendem Busverkehr einen Mittelwert –
kleine Abweichungen sind normal.

## 7. Zusammenbauen

1. Prüfspitzen entfernen, Stecker auf festen Sitz prüfen.
2. Controller/Blende einsetzen (ggf. Schrauben), Blende gleichmäßig
   einclipsen.
3. Zündung an, Controller drehen/drücken – reagiert das Radio-Menü normal?
4. Erscheint eine Check-Control-Meldung, verschwindet sie meist nach einem
   Schlafzyklus; sonst Fehlerspeicher mit Diagnosegerät löschen.

## 8. Ergebnistabelle (ausfüllen und schicken)

| Pin | Farbe | A: Zündung an (V) | B: gegen Masse, Ruhe (V) | B: beim Drehen (V) |
|---|---|---|---|---|
| 1 | | | – | – |
| 2 | | | – | – |
| 3 | | – | | |
| 4 | | – | | |

- C: Spannung Pin 3 → Pin 4 (mit Vorzeichen): ______ V
- D (optional): Widerstand Pin 3 ↔ Pin 4 schlafend: ______ Ω
- E: Pin 1 bei Zündung aus ___ V, abgeschlossen ___ V, nach 1 / 5 / 15 / 30 min: ___ / ___ / ___ / ___ V
- Fotos: Stecker von vorn/hinten, Adernfarben

## Quellen

- Pinbelegung Controller-Stecker (Pin 1 Kl. 30B, 2 Masse, 3 K-CAN H, 4 K-CAN L): https://www.bimmerfest.com/threads/retrofit-touch-controller.748522/
- Adernfarben K-CAN 1/K-CAN 2 im F30: https://f30.bimmerpost.com/forums/showthread.php?t=1777845 und https://f30.bimmerpost.com/forums/showthread.php?t=2022454
- Controller auf K-CAN 1 (CIC) vs. K-CAN 2 (NBT): https://f30.bimmerpost.com/forums/showthread.php?t=1954742
- Blende nur geclipst: https://f30.bimmerpost.com/forums/showthread/1086840/remove-the-idrive-trim
- K-CAN-Pegel älterer BMW (≈0,2 V / 4,8 V): https://www.e90post.com/forums/showthread.php?t=177272&page=2
- CAN-Messung mit Multimeter (60 Ω, Differenzmessung): https://pievcore.com/insights/how-to-measure-can-bus-health-with-a-multimeter-step-by-step-engineers-guide
