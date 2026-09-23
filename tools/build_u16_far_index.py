#!/usr/bin/env python3
"""Build sparse 16-bit ID pages containing GREEN 4-byte far pointers.

Each allocated page contains 256 entries. An entry is:
    little-endian u16 ROM bank + little-endian u16 CPU address

The caller uses the ID high byte to choose a page and the low byte to choose an
entry. Only pages that contain data need ROM space.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ENTRY_SIZE = 4
ENTRIES_PER_PAGE = 256
PAGE_SIZE = ENTRY_SIZE * ENTRIES_PER_PAGE
EMPTY = b"\xFF\xFF\xFF\xFF"
MAX_BANK = 0x1FF


def parse_int(text: str) -> int:
    return int(text, 0)


def encode_far(bank: int, address: int) -> bytes:
    if not 0 <= bank <= MAX_BANK:
        raise ValueError(f"bank out of MBC5 range: {bank:#x}")
    if not 0x4000 <= address <= 0x7FFF:
        raise ValueError(f"switchable-ROM address required: {address:#x}")
    return bank.to_bytes(2, "little") + address.to_bytes(2, "little")


def build_pages(entries: dict[int, tuple[int, int]]) -> dict[int, bytes]:
    pages: dict[int, bytearray] = {}
    for identity, (bank, address) in sorted(entries.items()):
        if not 0 <= identity <= 0xFFFF:
            raise ValueError(f"ID out of u16 range: {identity:#x}")
        page_id = identity >> 8
        slot = identity & 0xFF
        page = pages.setdefault(page_id, bytearray(EMPTY * ENTRIES_PER_PAGE))
        start = slot * ENTRY_SIZE
        if page[start:start + ENTRY_SIZE] != EMPTY:
            raise ValueError(f"duplicate ID: {identity:#06x}")
        page[start:start + ENTRY_SIZE] = encode_far(bank, address)
    return {key: bytes(value) for key, value in pages.items()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", type=Path, help="CSV with id,bank,address columns")
    ap.add_argument("output_dir", type=Path)
    args = ap.parse_args()

    entries: dict[int, tuple[int, int]] = {}
    with args.csv.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            identity = parse_int(row["id"])
            if identity in entries:
                raise SystemExit(f"duplicate ID in CSV: {identity:#06x}")
            entries[identity] = (parse_int(row["bank"]), parse_int(row["address"]))

    pages = build_pages(entries)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "schema_version": 1,
        "entry_size": ENTRY_SIZE,
        "entries_per_page": ENTRIES_PER_PAGE,
        "allocated_pages": [],
    }
    for page_id, payload in sorted(pages.items()):
        name = f"page_{page_id:02X}.bin"
        (args.output_dir / name).write_bytes(payload)
        manifest["allocated_pages"].append({
            "page": page_id,
            "file": name,
            "bytes": len(payload),
        })

    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
