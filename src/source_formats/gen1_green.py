"""Generation I Japanese Pocket Monsters Green source-format adapter.

This module describes input ROM/SAV layouts only. It does not define GREEN's
native GBA save format. Raw binaries remain local and are never committed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

CARTRIDGE_SRAM_SIZE = 0x8000
ROM_SIZE = 0x80000
ROM_BANK_SIZE = 0x4000
MAIN_DATA_START = 0x2598


@dataclass(frozen=True)
class SaveLayout:
    key: str
    checksum_offset: int
    box_count: int
    box_slots: int
    trainer_name_chars: int
    nickname_chars: int
    offsets: Mapping[str, int]


JAPANESE_GREEN_SAVE = SaveLayout(
    key="japanese-green",
    checksum_offset=0x3594,
    box_count=8,
    box_slots=30,
    trainer_name_chars=5,
    nickname_chars=5,
    offsets={
        "trainer_name": 0x2598,
        "dex_caught": 0x259E,
        "dex_seen": 0x25B1,
        "items": 0x25C4,
        "money": 0x25EE,
        "rival": 0x25F1,
        "options": 0x25F7,
        "badges": 0x25F8,
        "trainer_id": 0x25FB,
        "pc_items": 0x27DC,
        "current_box_index": 0x2842,
        "event_work": 0x2892,
        "starter": 0x29B9,
        "event_flags": 0x29E9,
        "play_time": 0x2CA0,
        "daycare": 0x2CA7,
        "party": 0x2ED5,
        "current_box": 0x302D,
    },
)


def normalize_raw_save(raw: bytes) -> tuple[bytes, bytes]:
    """Return the 32 KiB cartridge SRAM and any emulator-side tail bytes."""
    if len(raw) < CARTRIDGE_SRAM_SIZE:
        raise ValueError(f"save is shorter than cartridge SRAM: {len(raw)}")
    return raw[:CARTRIDGE_SRAM_SIZE], raw[CARTRIDGE_SRAM_SIZE:]


def rby_checksum(sram: bytes, layout: SaveLayout = JAPANESE_GREEN_SAVE) -> int:
    """Compute the Japanese Gen I one's-complement main-save checksum."""
    if len(sram) != CARTRIDGE_SRAM_SIZE:
        raise ValueError("checksum input must be normalized 32 KiB SRAM")
    return (~sum(sram[MAIN_DATA_START:layout.checksum_offset])) & 0xFF


def checksum_valid(sram: bytes, layout: SaveLayout = JAPANESE_GREEN_SAVE) -> bool:
    return sram[layout.checksum_offset] == rby_checksum(sram, layout)


def require_green_save(sram: bytes) -> SaveLayout:
    """Require the verified Japanese Green-family SRAM layout."""
    if len(sram) != CARTRIDGE_SRAM_SIZE:
        raise ValueError(f"unexpected Green SRAM size: {len(sram)}")
    if not checksum_valid(sram):
        raise ValueError("invalid Japanese Green main-save checksum")
    return JAPANESE_GREEN_SAVE


def parse_gb_header(rom: bytes) -> dict[str, int | str | bool]:
    """Parse cartridge facts required before Green source extraction."""
    if len(rom) < 0x150:
        raise ValueError("ROM is too small for a Game Boy header")

    rom_sizes = {
        0x00: 32768,
        0x01: 65536,
        0x02: 131072,
        0x03: 262144,
        0x04: 524288,
        0x05: 1048576,
        0x06: 2097152,
        0x07: 4194304,
        0x08: 8388608,
    }
    ram_sizes = {
        0x00: 0,
        0x01: 2048,
        0x02: 8192,
        0x03: 32768,
        0x04: 131072,
        0x05: 65536,
    }

    check = 0
    for value in rom[0x134:0x14D]:
        check = (check - value - 1) & 0xFF

    stored_global = (rom[0x14E] << 8) | rom[0x14F]
    calculated_global = (sum(rom[:0x14E]) + sum(rom[0x150:])) & 0xFFFF

    cart_code = rom[0x147]
    title = rom[0x134:0x144].split(b"\0", 1)[0].decode("ascii", "replace")

    return {
        "title": title,
        "rom_bytes": len(rom),
        "banks_16k": len(rom) // ROM_BANK_SIZE,
        "cartridge_type_code": cart_code,
        "cartridge_type": "MBC1+RAM+BATTERY" if cart_code == 0x03 else f"0x{cart_code:02X}",
        "declared_rom_bytes": rom_sizes.get(rom[0x148], -1),
        "declared_sram_bytes": ram_sizes.get(rom[0x149], -1),
        "header_version": rom[0x14C],
        "header_checksum_valid": rom[0x14D] == check,
        "global_checksum_valid": stored_global == calculated_global,
    }


def require_green_rom(rom: bytes) -> dict[str, int | str | bool]:
    """Reject inputs that do not match the verified Japanese Green cartridge profile."""
    info = parse_gb_header(rom)
    if info["title"] != "POKEMON GREEN":
        raise ValueError(f"unexpected title: {info['title']}")
    if info["rom_bytes"] != ROM_SIZE or info["declared_rom_bytes"] != ROM_SIZE:
        raise ValueError("unexpected Japanese Green ROM size")
    if info["cartridge_type_code"] != 0x03:
        raise ValueError("unexpected Japanese Green cartridge controller")
    if info["declared_sram_bytes"] != CARTRIDGE_SRAM_SIZE:
        raise ValueError("unexpected Japanese Green SRAM size")
    if info["header_version"] not in (0, 1):
        raise ValueError("unsupported Japanese Green revision")
    if not info["header_checksum_valid"] or not info["global_checksum_valid"]:
        raise ValueError("invalid Game Boy header/global checksum")
    return info
