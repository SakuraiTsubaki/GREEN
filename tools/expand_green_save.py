#!/usr/bin/env python3
"""Expand a 32 KiB Japanese Green SRAM image to 128 KiB.

Banks 0-3 are copied byte-for-byte. Bank 4 receives a small versioned extension
header; the rest of the new SRAM is 0xFF.
"""
from __future__ import annotations

import argparse
import struct
import zlib
from pathlib import Path

SOURCE_SIZE = 0x8000
TARGET_SIZE = 0x20000
BANK_SIZE = 0x2000
EXT_BANK = 4
EXT_OFFSET = EXT_BANK * BANK_SIZE
MAGIC = b"GRN10EXT"
SCHEMA_VERSION = 1
MAIN_DATA_START = 0x2598
CHECKSUM_OFFSET = 0x3594


def legacy_checksum(data: bytes) -> int:
    return (~sum(data[MAIN_DATA_START:CHECKSUM_OFFSET])) & 0xFF


def validate_source(data: bytes) -> None:
    if len(data) != SOURCE_SIZE:
        raise ValueError(f"expected 32 KiB source save, got {len(data)} bytes")
    if data[CHECKSUM_OFFSET] != legacy_checksum(data):
        raise ValueError("invalid Japanese Green main-save checksum")


def expand_save(data: bytes, revision: int) -> bytes:
    validate_source(data)
    if revision not in (0, 1):
        raise ValueError("revision must be 0 or 1")

    out = bytearray(b"\xFF" * TARGET_SIZE)
    out[:SOURCE_SIZE] = data

    payload_length = 0
    payload_crc32 = zlib.crc32(b"") & 0xFFFFFFFF
    header = struct.pack(
        "<8sHBBIII",
        MAGIC,
        SCHEMA_VERSION,
        revision,
        0,
        payload_length,
        payload_crc32,
        0,
    )
    out[EXT_OFFSET:EXT_OFFSET + len(header)] = header
    return bytes(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--revision", type=int, choices=(0, 1), required=True)
    args = ap.parse_args()

    source = args.source.read_bytes()
    expanded = expand_save(source, args.revision)
    if expanded[:SOURCE_SIZE] != source:
        raise SystemExit("legacy 32 KiB preservation check failed")
    args.output.write_bytes(expanded)
    print(f"GREEN save: {len(source)} -> {len(expanded)} bytes; legacy banks preserved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
