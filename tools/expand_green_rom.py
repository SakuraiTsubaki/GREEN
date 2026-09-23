#!/usr/bin/env python3
"""Expand verified Japanese Pocket Monsters Green to an 8 MiB MBC5 ROM.

The original Game Boy engine remains the runtime. This transformation:
- grows the ROM from 512 KiB to 8 MiB;
- migrates the cartridge header from MBC1+RAM+BATTERY to MBC5+RAM+BATTERY;
- declares 128 KiB external RAM;
- installs a fixed-bank 9-bit far-call bridge in audited pre-header space;
- initializes the MBC5 ninth ROM-bank bit before entering the original game;
- preserves every original byte outside explicitly audited patch locations and
  required header/checksum fields.

ROM binaries are generated locally and are never committed.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

SOURCE_SIZE = 0x80000
TARGET_SIZE = 0x800000
SOURCE_CART = 0x03
SOURCE_ROM_SIZE = 0x04
SOURCE_RAM_SIZE = 0x03
TARGET_CART = 0x1B
TARGET_ROM_SIZE = 0x08
TARGET_RAM_SIZE = 0x04

ENTRYPOINT = 0x0100
ORIGINAL_ENTRY = bytes((0x00, 0xC3, 0x50, 0x01))  # NOP; JP $0150
BRIDGE_LOW_ENTRY = 0x0068
BRIDGE_HIGH_ENTRY = 0x006D
BRIDGE_COMMON = 0x0070
BRIDGE_RETURN_LOW = 0x0081
BRIDGE_RETURN_HIGH = 0x0087
BRIDGE_RESTORE = 0x008C
BRIDGE_END = 0x0094
MBC5_INIT = 0x0094
MBC5_INIT_END = 0x009B

# FarCall9 ABI:
#   B  = target ROM-bank low byte
#   C  = target ROM-bank high bit (bit 0)
#   HL = target address in $4000-$7FFF
#
# Call $0068 when the caller lives in bank $000-$0FF.
# Call $006D when the caller lives in bank $100-$1FF.
#
# Two entry points encode the caller's high bank bit in the selected return
# trampoline, so nested high-bank far calls do not need a new WRAM/HRAM byte.
MBC5_BRIDGE = bytes((
    0x11, 0x81, 0x00,       # 0068: ld de,$0081
    0x18, 0x03,             # 006B: jr $0070
    0x11, 0x87, 0x00,       # 006D: ld de,$0087
    0xF0, 0xB8,             # 0070: ldh a,($FFB8) ; legacy loaded-bank low
    0xF5,                   #       push af
    0x78,                   #       ld a,b
    0xE0, 0xB8,             #       ldh ($FFB8),a
    0xEA, 0x00, 0x20,       #       ld ($2000),a  ; MBC5 low 8 bits
    0x79,                   #       ld a,c
    0xE6, 0x01,             #       and $01
    0xEA, 0x00, 0x30,       #       ld ($3000),a  ; MBC5 ninth bit
    0xD5,                   #       push de       ; selected return trampoline
    0xE9,                   #       jp hl
    0xAF,                   # 0081: xor a
    0xEA, 0x00, 0x30,       #       ld ($3000),a
    0x18, 0x05,             #       jr $008C
    0x3E, 0x01,             # 0087: ld a,$01
    0xEA, 0x00, 0x30,       #       ld ($3000),a
    0xC1,                   # 008C: pop bc        ; saved AF -> B=old low bank
    0x78,                   #       ld a,b
    0xE0, 0xB8,             #       ldh ($FFB8),a
    0xEA, 0x00, 0x20,       #       ld ($2000),a
    0xC9,                   #       ret
))

MBC5_INIT_BYTES = bytes((
    0xAF,                   # 0094: xor a
    0xEA, 0x00, 0x30,       #       ld ($3000),a
    0xC3, 0x50, 0x01,       #       jp $0150
))

NEW_ENTRY = bytes((0x00, 0xC3, MBC5_INIT & 0xFF, MBC5_INIT >> 8))

KNOWN = {
    "6576b4e0979e93d4a6fa02db893c294b7aeab3b841b1acc8658bc10b3554f33c": 0,
    "3f0dc460ca8d06be1c9ac96307c939c0ea7baa366b40c2f1f4ad63242b6c4816": 1,
}

AUDITED_LEGACY_PATCH_OFFSETS = (
    set(range(BRIDGE_LOW_ENTRY, MBC5_INIT_END))
    | {0x102, 0x103, 0x147, 0x148, 0x149, 0x14D, 0x14E, 0x14F}
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def header_checksum(data: bytes) -> int:
    value = 0
    for offset in range(0x134, 0x14D):
        value = (value - data[offset] - 1) & 0xFF
    return value


def global_checksum(data: bytes) -> int:
    return (sum(data[:0x14E]) + sum(data[0x150:])) & 0xFFFF


def validate_source(data: bytes) -> int:
    if len(data) != SOURCE_SIZE:
        raise ValueError(f"expected 512 KiB source ROM, got {len(data)} bytes")
    if data[ENTRYPOINT:ENTRYPOINT + 4] != ORIGINAL_ENTRY:
        raise ValueError("unexpected Green entrypoint")
    if data[0x134:0x144].split(b"\0", 1)[0] != b"POKEMON GREEN":
        raise ValueError("not a Japanese Pocket Monsters Green ROM header")
    if data[0x147] != SOURCE_CART:
        raise ValueError(f"unexpected source cartridge type 0x{data[0x147]:02X}")
    if data[0x148] != SOURCE_ROM_SIZE or data[0x149] != SOURCE_RAM_SIZE:
        raise ValueError("unexpected source ROM/RAM size code")
    digest = sha256(data)
    if digest not in KNOWN:
        raise ValueError(f"unverified Green ROM sha256: {digest}")
    revision = KNOWN[digest]
    if data[0x14C] != revision:
        raise ValueError("hash/revision mismatch")
    if data[0x14D] != header_checksum(data):
        raise ValueError("invalid source header checksum")
    if int.from_bytes(data[0x14E:0x150], "big") != global_checksum(data):
        raise ValueError("invalid source global checksum")
    return revision


def install_mbc5_bridge(out: bytearray) -> None:
    if len(MBC5_BRIDGE) != BRIDGE_END - BRIDGE_LOW_ENTRY:
        raise AssertionError("bridge layout changed without updating addresses")
    if len(MBC5_INIT_BYTES) != MBC5_INIT_END - MBC5_INIT:
        raise AssertionError("init layout changed without updating addresses")

    out[BRIDGE_LOW_ENTRY:BRIDGE_END] = MBC5_BRIDGE
    out[MBC5_INIT:MBC5_INIT_END] = MBC5_INIT_BYTES
    out[ENTRYPOINT:ENTRYPOINT + 4] = NEW_ENTRY


def expand_rom(data: bytes) -> bytes:
    validate_source(data)
    out = bytearray(data)
    out.extend(b"\xFF" * (TARGET_SIZE - len(out)))

    install_mbc5_bridge(out)

    out[0x147] = TARGET_CART
    out[0x148] = TARGET_ROM_SIZE
    out[0x149] = TARGET_RAM_SIZE
    out[0x14D] = header_checksum(out)

    out[0x14E:0x150] = b"\x00\x00"
    checksum = global_checksum(out)
    out[0x14E] = checksum >> 8
    out[0x14F] = checksum & 0xFF
    return bytes(out)


def unexpected_legacy_differences(source: bytes, expanded: bytes) -> list[int]:
    return [
        i
        for i in range(SOURCE_SIZE)
        if source[i] != expanded[i] and i not in AUDITED_LEGACY_PATCH_OFFSETS
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()

    source = args.source.read_bytes()
    revision = validate_source(source)
    expanded = expand_rom(source)

    unexpected = unexpected_legacy_differences(source, expanded)
    if unexpected:
        raise SystemExit(
            "legacy 512 KiB preservation check failed at: "
            + ", ".join(f"0x{x:X}" for x in unexpected[:20])
        )

    args.output.write_bytes(expanded)
    print(
        f"GREEN Rev {revision}: {len(source)} -> {len(expanded)} bytes; "
        f"MBC5 8 MiB / 128 KiB SRAM; FarCall9=$0068/$006D"
    )
    print(f"sha256={sha256(expanded)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
