#!/usr/bin/env python3
"""Install GREEN's 16-bit species resolver on the verified MBC5 ROM scaffold.

Input must be an 8 MiB image produced by tools/expand_green_rom.py at the
verified MBC5-bridge baseline.

Runtime API at bank 0x20:$4000
--------------------------------
Input:
    DE = canonical u16 species ID

Return:
    carry clear, A=0:
        legacy species 1..151 was loaded through the original Green loader;
        the original 28-byte work buffer at D095 is ready.

    carry clear, A=1:
        expanded species was resolved through the sparse paged index;
        BC = record ROM bank (little-endian u16 value in C:B)
        DE = record CPU address (E:D bytes represent the stored u16 address)

    carry set:
        ID is zero or no expanded record is installed.

The resolver consumes no speculative WRAM/HRAM. A fixed-bank helper at $009B
can read one four-byte far pointer from any MBC5 ROM bank and restores the
current low-bank caller afterwards.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

ROM_SIZE = 0x800000

READ4_HELPER = 0x009B
READ4_HELPER_END = 0x00BD

RUNTIME_BANK = 0x20
RUNTIME_CPU = 0x4000
RUNTIME_FILE_OFFSET = RUNTIME_BANK * 0x4000
RUNTIME_END = 0x407D

PAGE_DIRECTORY_CPU = 0x4100
PAGE_DIRECTORY_FILE_OFFSET = RUNTIME_FILE_OFFSET + (PAGE_DIRECTORY_CPU - 0x4000)
PAGE_DIRECTORY_ENTRIES = 256
PAGE_DIRECTORY_BYTES = PAGE_DIRECTORY_ENTRIES * 4

INPUTS = {
    "e1b4df8525b28f0b6fe18550815b3c91c38efe7c91b5ccae330b7344fe9beb99": {
        "revision": 0,
        "legacy_loader": 0x2F2E,
    },
    "93ff1f26e83ed3316d7c360debdca2dcaa2d0fbbc3e897bfd9cffa186ca1cafc": {
        "revision": 1,
        "legacy_loader": 0x2F1C,
    },
}

EXPECTED_OUTPUTS = {
    0: "fc860441941eb8f735fc96bddbc3e20c046aa2e30d0d4acb9871fc2e604dc2fe",
    1: "d146d472e26e1709a650b94dfe979fcc0d25be52538f645a7cf6f05069c2bfe7",
}

# Input: B=target bank low, C=target bank bit 8, HL=source address.
# Output: B,C,D,E = four bytes read from source.
# This entry is intentionally for a caller whose current bank bit 8 is zero;
# GREEN's species resolver lives in bank 0x20.
READ4_FROM_BANK9_LOW = bytes((
    0xF0, 0xB8,             # ldh a,(FFB8) ; save current low bank
    0xF5,                   # push af
    0x78,                   # ld a,b
    0xE0, 0xB8,             # ldh (FFB8),a
    0xEA, 0x00, 0x20,       # ld (2000),a
    0x79,                   # ld a,c
    0xE6, 0x01,             # and 1
    0xEA, 0x00, 0x30,       # ld (3000),a
    0x2A, 0x47,             # ld a,(hl+); ld b,a
    0x2A, 0x4F,             # ld a,(hl+); ld c,a
    0x2A, 0x57,             # ld a,(hl+); ld d,a
    0x7E, 0x5F,             # ld a,(hl);  ld e,a
    0xAF,                   # xor a
    0xEA, 0x00, 0x30,       # restore caller bank bit 8 = 0
    0xF1,                   # pop af
    0xE0, 0xB8,             # ldh (FFB8),a
    0xEA, 0x00, 0x20,       # ld (2000),a
    0xC9,                   # ret
))


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def global_checksum(data: bytes) -> int:
    return (sum(data[:0x14E]) + sum(data[0x150:])) & 0xFFFF


def runtime_code(legacy_loader: int) -> bytes:
    """Build the revision-specific resolver at bank 0x20:$4000."""
    # Absolute labels for this fixed layout.
    expanded = 0x4038
    dir_ok = 0x4058
    found = 0x4076
    missing_pop = 0x407A
    missing = 0x407B

    return bytes((
        0x7A,                         # 4000 ld a,d
        0xB7,                         #      or a
        0xC2, expanded & 0xFF, expanded >> 8, # jp nz,expanded
        0x7B,                         # 4005 ld a,e
        0xB7,                         #      or a
        0xCA, missing & 0xFF, missing >> 8,   # jp z,missing
        0xFE, 0x98,                   # 400A cp 152
        0xD2, expanded & 0xFF, expanded >> 8, # jp nc,expanded

        # Legacy canonical Dex 1..151 -> original internal ID -> original loader.
        0xFA, 0x92, 0xD0,             # 400F ld a,(D092)
        0xF5,                         #      push af
        0xFA, 0xE3, 0xD0,             # 4013 ld a,(D0E3)
        0xF5,                         #      push af
        0x7B,                         # 4017 ld a,e
        0xEA, 0xE3, 0xD0,             #      ld (D0E3),a
        0x06, 0x10,                   # 401B ld b,10
        0x0E, 0x00,                   # 401D ld c,0
        0x21, 0x6F, 0x67,             # 401F ld hl,676F ; Dex->internal
        0xCD, 0x68, 0x00,             # 4022 call FarCall9FromLow
        0xFA, 0xE3, 0xD0,             # 4025 ld a,(D0E3)
        0xEA, 0x92, 0xD0,             #      ld (D092),a
        0xCD, legacy_loader & 0xFF, legacy_loader >> 8,
        0xF1,                         # 402E pop af
        0xEA, 0xE3, 0xD0,             #      restore D0E3
        0xF1,                         # 4032 pop af
        0xEA, 0x92, 0xD0,             #      restore D092
        0xAF,                         # 4036 xor a ; A=0, clear carry
        0xC9,                         #      ret

        # Expanded ID path. High byte selects the directory page.
        0x7B,                         # 4038 ld a,e ; save slot low byte
        0xF5,                         #      push af
        0x7A,                         #      ld a,d
        0x6F,                         #      ld l,a
        0x26, 0x00,                   #      ld h,0
        0x29, 0x29,                   #      hl *= 4
        0x01, 0x00, 0x41,             #      ld bc,4100
        0x09,                         #      add hl,bc
        0x2A, 0x47,                   #      directory bank low -> B
        0x2A, 0x4F,                   #      directory bank high -> C
        0x2A, 0x57,                   #      directory address low -> D
        0x7E, 0x5F,                   #      directory address high -> E
        0x78, 0xFE, 0xFF,             #      bank low == FF?
        0xC2, dir_ok & 0xFF, dir_ok >> 8,
        0x79, 0xFE, 0xFF,             #      bank high == FF?
        0xCA, missing_pop & 0xFF, missing_pop >> 8,

        # BC: page bank, DE: page base address.
        0x62, 0x6B,                   # 4058 ld h,d; ld l,e
        0xF1,                         #      pop af ; slot low byte
        0x5F,                         #      ld e,a
        0x16, 0x00,                   #      ld d,0
        0xCB, 0x23,                   #      sla e
        0xCB, 0x12,                   #      rl d
        0xCB, 0x23,                   #      sla e
        0xCB, 0x12,                   #      rl d ; DE = slot * 4
        0x19,                         #      add hl,de
        0xCD, READ4_HELPER & 0xFF, READ4_HELPER >> 8,
        0x78, 0xFE, 0xFF,             #      record bank low == FF?
        0xC2, found & 0xFF, found >> 8,
        0x79, 0xFE, 0xFF,             #      record bank high == FF?
        0xCA, missing & 0xFF, missing >> 8,

        0x3E, 0x01,                   # 4076 ld a,1 ; expanded pointer result
        0xB7,                         #      or a ; clear carry
        0xC9,                         #      ret
        0xF1,                         # 407A pop af ; missing directory page
        0x37,                         # 407B scf
        0xC9,                         #      ret
    ))


def patch(data: bytes) -> tuple[int, bytes]:
    if len(data) != ROM_SIZE:
        raise ValueError(f"expected 8 MiB MBC5 image, got {len(data)} bytes")

    digest = sha256(data)
    try:
        profile = INPUTS[digest]
    except KeyError:
        raise ValueError(f"unverified MBC5 bridge baseline sha256: {digest}") from None

    revision = profile["revision"]
    code = runtime_code(profile["legacy_loader"])
    if len(READ4_FROM_BANK9_LOW) != READ4_HELPER_END - READ4_HELPER:
        raise AssertionError("fixed-bank read helper layout changed")
    if len(code) != RUNTIME_END - RUNTIME_CPU:
        raise AssertionError("species resolver layout changed")

    if data[READ4_HELPER:READ4_HELPER_END] != b"\xFF" * len(READ4_FROM_BANK9_LOW):
        raise ValueError("fixed-bank read helper destination is not empty")
    if data[RUNTIME_FILE_OFFSET:RUNTIME_FILE_OFFSET + len(code)] != b"\xFF" * len(code):
        raise ValueError("species resolver destination is not empty")
    if data[
        PAGE_DIRECTORY_FILE_OFFSET:
        PAGE_DIRECTORY_FILE_OFFSET + PAGE_DIRECTORY_BYTES
    ] != b"\xFF" * PAGE_DIRECTORY_BYTES:
        raise ValueError("species page directory is not empty")

    out = bytearray(data)
    out[READ4_HELPER:READ4_HELPER_END] = READ4_FROM_BANK9_LOW
    out[RUNTIME_FILE_OFFSET:RUNTIME_FILE_OFFSET + len(code)] = code

    out[0x14E:0x150] = b"\x00\x00"
    checksum = global_checksum(out)
    out[0x14E] = checksum >> 8
    out[0x14F] = checksum & 0xFF

    result = bytes(out)
    expected = EXPECTED_OUTPUTS[revision]
    actual = sha256(result)
    if actual != expected:
        raise AssertionError(f"unexpected patched image sha256: {actual}")
    return revision, result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()

    revision, result = patch(args.input.read_bytes())
    args.output.write_bytes(result)
    print(
        f"GREEN Rev {revision}: installed u16 species resolver at "
        f"bank 0x{RUNTIME_BANK:02X}:0x{RUNTIME_CPU:04X}"
    )
    print(f"sha256={sha256(result)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
