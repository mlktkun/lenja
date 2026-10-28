#!/usr/bin/env python3
"""Hilft, die iDrive- und Lenkradtasten-Botschaften am eigenen F30 zu finden.

Ablauf:
  1. CAN-Schnittstelle im listen-only-Modus starten (siehe deploy/can0.network)
  2. python tools/can_sniff.py --channel can0
  3. Phase "Ruhe": einige Sekunden NICHTS anfassen. Das Skript merkt sich,
     welche Bytes sich von allein ändern (Zähler, Prüfsummen, Sensoren).
  4. Phase "Beobachten": Controller drehen, Tasten drücken. Angezeigt werden
     nur Bytes, die in der Ruhephase stabil waren – das sind die Kandidaten.
  5. Gefundene Werte in config/idrive_map.toml eintragen.

Mit --log datei.log wird alles zusätzlich im candump-Format mitgeschrieben;
die Datei kann später mit CARPI_CAN_REPLAY=datei.log abgespielt werden.
"""

from __future__ import annotations

import argparse
import time
from collections import defaultdict

import can


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--interface", default="socketcan")
    parser.add_argument("--channel", default="can0")
    parser.add_argument("--replay", help="statt Live-Bus eine Log-Datei lesen")
    parser.add_argument("--quiet-seconds", type=float, default=10.0, help="Dauer der Ruhephase")
    parser.add_argument("--log", help="alle Frames im candump-Format mitschreiben")
    args = parser.parse_args()

    source = can.LogReader(args.replay) if args.replay else can.Bus(interface=args.interface, channel=args.channel)
    logger = can.Logger(args.log) if args.log else None

    last: dict[int, bytes] = {}
    noisy: dict[int, set[int]] = defaultdict(set)  # ID -> Bytepositionen, die sich in Ruhe ändern
    start = time.monotonic()
    quiet = True
    print(f"Ruhephase: {args.quiet_seconds:.0f} s nichts anfassen …")

    try:
        for msg in source:
            if msg is None:
                continue
            if logger:
                logger(msg)
            data, can_id = bytes(msg.data), msg.arbitration_id
            previous = last.get(can_id)
            last[can_id] = data

            if quiet and time.monotonic() - start > args.quiet_seconds:
                quiet = False
                print(f"Beobachten: {len(last)} IDs bekannt. Jetzt drehen/drücken. Strg+C zum Beenden.\n")
            if previous is None or previous == data:
                continue

            changed = [i for i in range(min(len(data), len(previous))) if data[i] != previous[i]]
            if quiet:
                noisy[can_id].update(changed)
                continue
            interesting = [i for i in changed if i not in noisy[can_id]]
            if interesting:
                detail = ", ".join(f"Byte {i}: {previous[i]:02X}→{data[i]:02X}" for i in interesting)
                print(f"0x{can_id:03X}  [{data.hex(' ')}]  {detail}")
    except KeyboardInterrupt:
        pass
    finally:
        if logger:
            logger.stop()
        if hasattr(source, "shutdown"):
            source.shutdown()


if __name__ == "__main__":
    main()
