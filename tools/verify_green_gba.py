#!/usr/bin/env python3
"""Verify a built GREEN GBA image without committing the ROM."""
from __future__ import annotations

import argparse
from pathlib import Path

MAX_ROM_BYTES = 32 * 1024 * 1024
EXPECTED_TITLE = b"PM GREEN REM"
EXPECTED_GAME_CODE = b"GRXJ"
EXPECTED_MAKER = b"00"


def gba_header_checksum(rom: bytes) -> int:
    value = 0
    for b in rom[0xA0:0xBD]:
        value = (value - b) & 0xFF
    return (value - 0x19) & 0xFF


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    args = ap.parse_args()

    rom = args.rom.read_bytes()
    if len(rom) > MAX_ROM_BYTES:
        raise SystemExit(f"ROM exceeds 32 MiB GBA ceiling: {len(rom)} bytes")
    if len(rom) < 0xC0:
        raise SystemExit("ROM is too small for a GBA header")

    title = rom[0xA0:0xAC]
    code = rom[0xAC:0xB0]
    maker = rom[0xB0:0xB2]
    fixed = rom[0xB2]
    version = rom[0xBC]
    stored = rom[0xBD]
    calculated = gba_header_checksum(rom)

    if title != EXPECTED_TITLE:
        raise SystemExit(f"unexpected title: {title!r}")
    if code != EXPECTED_GAME_CODE:
        raise SystemExit(f"unexpected game code: {code!r}")
    if maker != EXPECTED_MAKER:
        raise SystemExit(f"unexpected maker code: {maker!r}")
    if fixed != 0x96:
        raise SystemExit(f"invalid fixed header byte: 0x{fixed:02X}")
    if stored != calculated:
        raise SystemExit(
            f"invalid GBA header checksum: stored=0x{stored:02X} calculated=0x{calculated:02X}"
        )

    print(f"GREEN GBA image: OK ({len(rom)} bytes, {len(rom)/(1024*1024):.2f} MiB)")
    print(
        f"title={title.decode('ascii')} code={code.decode('ascii')} "
        f"maker={maker.decode('ascii')} revision={version}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
