#!/usr/bin/env python3
"""Expand a verified Japanese Green ROM to an 8 MiB MBC5 image scaffold.

The first 512 KiB is preserved except the cartridge mapper/size fields and
header/global checksums. New banks are initialized to 0xFF.

This tool does not claim that all new banks are reachable until the bank-switch
runtime is patched and verified.
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

KNOWN = {
    "6576b4e0979e93d4a6fa02db893c294b7aeab3b841b1acc8658bc10b3554f33c": 0,
    "3f0dc460ca8d06be1c9ac96307c939c0ea7baa366b40c2f1f4ad63242b6c4816": 1,
}


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


def expand_rom(data: bytes) -> bytes:
    validate_source(data)
    out = bytearray(data)
    out.extend(b"\xFF" * (TARGET_SIZE - len(out)))
    out[0x147] = TARGET_CART
    out[0x148] = TARGET_ROM_SIZE
    out[0x149] = TARGET_RAM_SIZE
    out[0x14D] = header_checksum(out)
    out[0x14E:0x150] = b"\x00\x00"
    checksum = global_checksum(out)
    out[0x14E] = checksum >> 8
    out[0x14F] = checksum & 0xFF
    return bytes(out)


def preserved_legacy_bytes(source: bytes, expanded: bytes) -> bool:
    ignored = {0x147, 0x148, 0x149, 0x14D, 0x14E, 0x14F}
    return all(
        source[i] == expanded[i]
        for i in range(SOURCE_SIZE)
        if i not in ignored
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()

    source = args.source.read_bytes()
    revision = validate_source(source)
    expanded = expand_rom(source)
    if not preserved_legacy_bytes(source, expanded):
        raise SystemExit("legacy 512 KiB preservation check failed")
    args.output.write_bytes(expanded)
    print(
        f"GREEN Rev {revision}: {len(source)} -> {len(expanded)} bytes; "
        f"MBC5 8 MiB / 128 KiB SRAM header"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
