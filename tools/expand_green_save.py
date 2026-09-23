#!/usr/bin/env python3
"""Expand a Japanese Green 32 KiB SRAM image to 128 KiB MBC5 SRAM.

Banks 0-3 are copied byte-for-byte. Bank 4 starts GREEN's versioned extension.
The migration reads the paired verified ROM's actual 190-byte internal-species
mapping table so party species are converted from legacy internal IDs to a
16-bit canonical base-species identity.

ROM/SAV binaries remain local and are never committed.
"""
from __future__ import annotations

import argparse
import hashlib
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

SPECIES_MAP_ROM_OFFSET = 0x4279A
SPECIES_MAP_COUNT = 190
PARTY_BLOCK_OFFSET = 0x2ED5
PARTY_COUNT_OFFSET = PARTY_BLOCK_OFFSET
PARTY_SPECIES_LIST_OFFSET = PARTY_BLOCK_OFFSET + 1
PARTY_SLOTS = 6

EXT_PAYLOAD_LOCAL_OFFSET = 0x20
EXT_PAYLOAD_OFFSET = EXT_OFFSET + EXT_PAYLOAD_LOCAL_OFFSET
PARTY_IDENTITY_ENTRY_SIZE = 4
PARTY_IDENTITY_BYTES = PARTY_SLOTS * PARTY_IDENTITY_ENTRY_SIZE
INVALID_SPECIES_ID = 0xFFFF

KNOWN_ROMS = {
    "6576b4e0979e93d4a6fa02db893c294b7aeab3b841b1acc8658bc10b3554f33c": 0,
    "3f0dc460ca8d06be1c9ac96307c939c0ea7baa366b40c2f1f4ad63242b6c4816": 1,
}


def legacy_checksum(data: bytes) -> int:
    return (~sum(data[MAIN_DATA_START:CHECKSUM_OFFSET])) & 0xFF


def validate_source(data: bytes) -> None:
    if len(data) != SOURCE_SIZE:
        raise ValueError(f"expected 32 KiB source save, got {len(data)} bytes")
    if data[CHECKSUM_OFFSET] != legacy_checksum(data):
        raise ValueError("invalid Japanese Green main-save checksum")


def species_map_from_rom(rom: bytes) -> tuple[int, bytes]:
    digest = hashlib.sha256(rom).hexdigest()
    try:
        revision = KNOWN_ROMS[digest]
    except KeyError:
        raise ValueError(f"unverified Green ROM sha256: {digest}") from None

    table = rom[SPECIES_MAP_ROM_OFFSET:SPECIES_MAP_ROM_OFFSET + SPECIES_MAP_COUNT]
    if len(table) != SPECIES_MAP_COUNT:
        raise ValueError("truncated internal species mapping table")
    if table[0x15 - 1] != 151:
        raise ValueError("verified Mew mapping invariant failed")
    if table[0x99 - 1] != 1:
        raise ValueError("verified Bulbasaur mapping invariant failed")
    return revision, table


def canonical_species_id(internal_id: int, species_map: bytes) -> int:
    if internal_id == 0:
        return 0
    if 1 <= internal_id <= len(species_map):
        dex = species_map[internal_id - 1]
        return dex if dex else INVALID_SPECIES_ID
    return INVALID_SPECIES_ID


def build_party_identity_payload(save: bytes, species_map: bytes) -> bytes:
    count = save[PARTY_COUNT_OFFSET]
    if count > PARTY_SLOTS:
        raise ValueError(f"invalid party count: {count}")

    payload = bytearray()
    for slot in range(PARTY_SLOTS):
        internal_id = save[PARTY_SPECIES_LIST_OFFSET + slot]
        species_id = (
            canonical_species_id(internal_id, species_map)
            if slot < count
            else 0
        )
        form_id = 0
        payload += species_id.to_bytes(2, "little")
        payload += form_id.to_bytes(2, "little")
    return bytes(payload)


def expand_save(data: bytes, revision: int, species_map: bytes) -> bytes:
    validate_source(data)
    if revision not in (0, 1):
        raise ValueError("revision must be 0 or 1")
    if len(species_map) != SPECIES_MAP_COUNT:
        raise ValueError("unexpected species mapping table size")

    out = bytearray(b"\xFF" * TARGET_SIZE)
    out[:SOURCE_SIZE] = data

    payload = build_party_identity_payload(data, species_map)
    payload_crc32 = zlib.crc32(payload) & 0xFFFFFFFF

    header = struct.pack(
        "<8sHBBIII",
        MAGIC,
        SCHEMA_VERSION,
        revision,
        0,
        len(payload),
        payload_crc32,
        0,
    )
    out[EXT_OFFSET:EXT_OFFSET + len(header)] = header
    out[EXT_PAYLOAD_OFFSET:EXT_PAYLOAD_OFFSET + len(payload)] = payload
    return bytes(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--rom", type=Path, required=True)
    args = ap.parse_args()

    source = args.source.read_bytes()
    rom = args.rom.read_bytes()
    revision, species_map = species_map_from_rom(rom)
    expanded = expand_save(source, revision, species_map)

    if expanded[:SOURCE_SIZE] != source:
        raise SystemExit("legacy 32 KiB preservation check failed")

    args.output.write_bytes(expanded)
    digest = hashlib.sha256(expanded).hexdigest()
    print(
        f"GREEN Rev {revision}: save {len(source)} -> {len(expanded)} bytes; "
        "legacy banks preserved; party u16 species/form sidecar initialized"
    )
    print(f"sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
