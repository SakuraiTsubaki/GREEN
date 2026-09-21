#!/usr/bin/env python3
"""Reproduce GREEN ROM/save baseline observations without storing the binaries."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROM_BANK = 0x4000
RAM_BANK = 0x2000


def hashes(data: bytes) -> dict[str, str]:
    return {
        "md5": hashlib.md5(data).hexdigest(),
        "sha1": hashlib.sha1(data).hexdigest(),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def header_checksum(data: bytes) -> int:
    value = 0
    for offset in range(0x134, 0x14D):
        value = (value - data[offset] - 1) & 0xFF
    return value


def global_checksum(data: bytes) -> int:
    return sum(data[:0x14E] + data[0x150:]) & 0xFFFF


def rom_info(path: Path) -> dict:
    data = path.read_bytes()
    if len(data) < 0x150:
        raise ValueError(f"{path}: too small for a Game Boy header")
    title = data[0x134:0x144].split(b"\0", 1)[0].decode("ascii", "replace")
    return {
        "path": str(path),
        "size": len(data),
        "hashes": hashes(data),
        "header": {
            "title": title,
            "sgb_flag": data[0x146],
            "cartridge_type": data[0x147],
            "rom_size_code": data[0x148],
            "ram_size_code": data[0x149],
            "destination_code": data[0x14A],
            "revision": data[0x14C],
            "header_checksum_stored": data[0x14D],
            "header_checksum_calculated": header_checksum(data),
            "global_checksum_stored": int.from_bytes(data[0x14E:0x150], "big"),
            "global_checksum_calculated": global_checksum(data),
        },
    }


def bank_diff(left: bytes, right: bytes, bank_size: int) -> list[dict]:
    if len(left) != len(right):
        raise ValueError("inputs must have equal size for bank comparison")
    rows = []
    for start in range(0, len(left), bank_size):
        end = min(start + bank_size, len(left))
        count = sum(a != b for a, b in zip(left[start:end], right[start:end]))
        rows.append({
            "bank": start // bank_size,
            "file_start": start,
            "file_end": end,
            "different_bytes": count,
        })
    return rows


def save_info(path: Path) -> dict:
    data = path.read_bytes()
    banks = []
    for start in range(0, len(data), RAM_BANK):
        chunk = data[start:start + RAM_BANK]
        non_ff = [i for i, value in enumerate(chunk) if value != 0xFF]
        banks.append({
            "bank": start // RAM_BANK,
            "file_start": start,
            "file_end": start + len(chunk),
            "non_ff_bytes": len(non_ff),
            "first_non_ff": min(non_ff) if non_ff else None,
            "last_non_ff": max(non_ff) if non_ff else None,
            "zero_bytes": chunk.count(0),
            "ff_bytes": chunk.count(0xFF),
            "unique_byte_values": len(set(chunk)),
        })
    return {
        "path": str(path),
        "size": len(data),
        "hashes": hashes(data),
        "banks": banks,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rev0-rom", required=True, type=Path)
    parser.add_argument("--reva-rom", required=True, type=Path)
    parser.add_argument("--rev0-save", required=True, type=Path)
    parser.add_argument("--reva-save", required=True, type=Path)
    args = parser.parse_args()

    rev0_rom = args.rev0_rom.read_bytes()
    reva_rom = args.reva_rom.read_bytes()
    rev0_save = args.rev0_save.read_bytes()
    reva_save = args.reva_save.read_bytes()

    report = {
        "rev0_rom": rom_info(args.rev0_rom),
        "reva_rom": rom_info(args.reva_rom),
        "rom_bank_diff": bank_diff(rev0_rom, reva_rom, ROM_BANK),
        "rom_total_different_bytes": sum(a != b for a, b in zip(rev0_rom, reva_rom)),
        "rev0_save": save_info(args.rev0_save),
        "reva_save": save_info(args.reva_save),
        "save_bank_diff": bank_diff(rev0_save, reva_save, RAM_BANK),
        "save_total_different_bytes": sum(a != b for a, b in zip(rev0_save, reva_save)),
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
