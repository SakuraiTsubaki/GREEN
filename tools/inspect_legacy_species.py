#!/usr/bin/env python3
"""Extract the verified Generation I Green base-stat records as CSV.

The source ROM stays local. The output is derived metadata suitable for review
or later conversion into GREEN's expanded 16-bit species namespace.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from pathlib import Path

STANDARD_OFFSET = 0x38000
STANDARD_BANK = 0x0E
STANDARD_CPU = 0x4000
STANDARD_COUNT = 150
RECORD_SIZE = 28
MEW_OFFSET = 0x4200
MEW_BANK = 0x01
MEW_CPU = 0x4200

KNOWN = {
    "6576b4e0979e93d4a6fa02db893c294b7aeab3b841b1acc8658bc10b3554f33c": "Rev 0",
    "3f0dc460ca8d06be1c9ac96307c939c0ea7baa366b40c2f1f4ad63242b6c4816": "Rev A",
}

FIELDS = (
    "national_dex", "source_kind", "bank", "cpu_address", "file_offset",
    "record_size", "hp", "attack", "defense", "speed", "special",
    "type1", "type2", "catch_rate", "base_exp", "sprite_dimensions",
    "front_pic_ptr", "back_pic_ptr", "move1", "move2", "move3", "move4",
    "growth_rate", "tmhm_hex", "raw_hex",
)


def verify_rom(data: bytes) -> str:
    digest = hashlib.sha256(data).hexdigest()
    try:
        return KNOWN[digest]
    except KeyError:
        raise ValueError(f"unverified Green ROM sha256: {digest}") from None


def decode_record(
    record: bytes,
    *,
    source_kind: str,
    bank: int,
    cpu_address: int,
    file_offset: int,
) -> dict[str, str | int]:
    if len(record) != RECORD_SIZE:
        raise ValueError("truncated base-stat record")
    return {
        "national_dex": record[0],
        "source_kind": source_kind,
        "bank": f"0x{bank:02X}",
        "cpu_address": f"0x{cpu_address:04X}",
        "file_offset": f"0x{file_offset:05X}",
        "record_size": RECORD_SIZE,
        "hp": record[1],
        "attack": record[2],
        "defense": record[3],
        "speed": record[4],
        "special": record[5],
        "type1": record[6],
        "type2": record[7],
        "catch_rate": record[8],
        "base_exp": record[9],
        "sprite_dimensions": f"0x{record[10]:02X}",
        "front_pic_ptr": f"0x{int.from_bytes(record[11:13], 'little'):04X}",
        "back_pic_ptr": f"0x{int.from_bytes(record[13:15], 'little'):04X}",
        "move1": record[15],
        "move2": record[16],
        "move3": record[17],
        "move4": record[18],
        "growth_rate": record[19],
        "tmhm_hex": record[20:28].hex(),
        "raw_hex": record.hex(),
    }


def extract_records(data: bytes) -> list[dict[str, str | int]]:
    verify_rom(data)
    rows: list[dict[str, str | int]] = []

    for dex in range(1, STANDARD_COUNT + 1):
        offset = STANDARD_OFFSET + (dex - 1) * RECORD_SIZE
        record = data[offset:offset + RECORD_SIZE]
        if record[0] != dex:
            raise ValueError(
                f"base table stopped being sequential at dex {dex}: "
                f"found {record[0]}"
            )
        rows.append(decode_record(
            record,
            source_kind="base-table",
            bank=STANDARD_BANK,
            cpu_address=STANDARD_CPU + (dex - 1) * RECORD_SIZE,
            file_offset=offset,
        ))

    mew = data[MEW_OFFSET:MEW_OFFSET + RECORD_SIZE]
    if mew[0] != 151:
        raise ValueError(f"unexpected Mew record dex byte: {mew[0]}")
    rows.append(decode_record(
        mew,
        source_kind="mew-special",
        bank=MEW_BANK,
        cpu_address=MEW_CPU,
        file_offset=MEW_OFFSET,
    ))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--compare", type=Path)
    args = ap.parse_args()

    data = args.rom.read_bytes()
    revision = verify_rom(data)
    rows = extract_records(data)

    if args.compare:
        other = args.compare.read_bytes()
        other_revision = verify_rom(other)
        other_rows = extract_records(other)
        if rows != other_rows:
            raise SystemExit(
                f"species records differ between {revision} and {other_revision}"
            )

    writer = csv.DictWriter(sys.stdout, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
