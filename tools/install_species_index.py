#!/usr/bin/env python3
"""Install sparse species-ID index pages into a GREEN expanded ROM.

Input CSV columns:
    id,bank,address

The record itself must already exist in an expansion record bank. This tool
only installs the ID -> far-pointer index.

Index layout
------------
Directory: bank 0x20:$4100, 256 x 4-byte far pointers.
Pages:     banks 0x21-0x30, deterministic 1 KiB slots.
Records:   must live in banks 0x31-0x1FF.

Page HH is stored at:
    bank = 0x21 + HH // 16
    cpu  = 0x4000 + (HH % 16) * 0x0400

This reserves exactly sixteen banks for the complete 65536-ID index surface,
while only populated pages are written.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from tools.build_u16_far_index import (
    EMPTY,
    ENTRY_SIZE,
    PAGE_SIZE,
    build_pages,
    encode_far,
)
from tools.patch_species_runtime import (
    PAGE_DIRECTORY_FILE_OFFSET,
    ROM_SIZE,
    global_checksum,
)

PAGE_BANK_FIRST = 0x21
PAGE_BANK_LAST = 0x30
RECORD_BANK_FIRST = 0x31
RECORD_BANK_LAST = 0x1FF


def parse_int(value: str) -> int:
    return int(value, 0)


def page_location(page_id: int) -> tuple[int, int]:
    if not 0 <= page_id <= 0xFF:
        raise ValueError("page ID out of range")
    bank = PAGE_BANK_FIRST + page_id // 16
    address = 0x4000 + (page_id % 16) * PAGE_SIZE
    return bank, address


def rom_offset(bank: int, address: int) -> int:
    if not PAGE_BANK_FIRST <= bank <= RECORD_BANK_LAST:
        raise ValueError(f"bank out of expansion range: {bank:#x}")
    if not 0x4000 <= address <= 0x7FFF:
        raise ValueError(f"switchable address required: {address:#x}")
    return bank * 0x4000 + (address - 0x4000)


def install_index(
    image: bytes,
    entries: dict[int, tuple[int, int]],
) -> bytes:
    if len(image) != ROM_SIZE:
        raise ValueError("expected 8 MiB GREEN image")

    for identity, (bank, address) in entries.items():
        if identity <= 151:
            raise ValueError(
                f"legacy species ID {identity} must stay on the original path"
            )
        if not RECORD_BANK_FIRST <= bank <= RECORD_BANK_LAST:
            raise ValueError(
                f"species record bank {bank:#x} overlaps runtime/index reservation"
            )
        if not 0x4000 <= address <= 0x7FFF:
            raise ValueError(f"invalid record address: {address:#x}")

    pages = build_pages(entries)
    out = bytearray(image)

    # Reset only the owned directory surface, then write allocated page pointers.
    out[
        PAGE_DIRECTORY_FILE_OFFSET:
        PAGE_DIRECTORY_FILE_OFFSET + 256 * ENTRY_SIZE
    ] = b"\xFF" * (256 * ENTRY_SIZE)

    for page_id, payload in pages.items():
        bank, address = page_location(page_id)
        page_off = rom_offset(bank, address)
        if out[page_off:page_off + PAGE_SIZE] != b"\xFF" * PAGE_SIZE:
            raise ValueError(
                f"species index page destination not empty: page {page_id:#04x}"
            )
        out[page_off:page_off + PAGE_SIZE] = payload

        dir_off = PAGE_DIRECTORY_FILE_OFFSET + page_id * ENTRY_SIZE
        out[dir_off:dir_off + ENTRY_SIZE] = encode_far(bank, address)

    out[0x14E:0x150] = b"\x00\x00"
    checksum = global_checksum(out)
    out[0x14E] = checksum >> 8
    out[0x14F] = checksum & 0xFF
    return bytes(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("mapping_csv", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()

    entries: dict[int, tuple[int, int]] = {}
    with args.mapping_csv.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            identity = parse_int(row["id"])
            if identity in entries:
                raise SystemExit(f"duplicate species ID: {identity:#06x}")
            entries[identity] = (
                parse_int(row["bank"]),
                parse_int(row["address"]),
            )

    result = install_index(args.rom.read_bytes(), entries)
    args.output.write_bytes(result)
    print(f"installed {len(entries)} species index entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
