#!/usr/bin/env python3
"""Scan raw Green ROM bytes for exact LD (nn),A mapper-control opcodes.

This is a byte-pattern census only. Hits must be promoted to executable-code
claims through control-flow analysis.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from pathlib import Path

TARGETS = (0x2000, 0x3000, 0x4000, 0x6000)


def positions(data: bytes, address: int) -> list[int]:
    pattern = bytes((0xEA, address & 0xFF, address >> 8))
    return [
        i for i in range(len(data) - 2)
        if data[i:i + 3] == pattern
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--revision", required=True)
    args = ap.parse_args()

    data = args.rom.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    writer = csv.writer(sys.stdout)
    writer.writerow(("revision", "sha256", "opcode", "target", "count", "positions"))
    for address in TARGETS:
        hits = positions(data, address)
        writer.writerow((
            args.revision,
            digest,
            "EA",
            f"0x{address:04X}",
            len(hits),
            " ".join(f"0x{x:X}" for x in hits),
        ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
