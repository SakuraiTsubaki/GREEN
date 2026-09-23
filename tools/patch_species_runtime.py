#!/usr/bin/env python3
"""Install GREEN's first 16-bit species runtime entry in expansion bank 0x20.

Input must be an 8 MiB image produced by tools/expand_green_rom.py at the
verified MBC5-bridge baseline.

Runtime ABI at bank 0x20:$4000:
    DE = canonical u16 species ID
Return:
    carry clear = legacy species 1..151 loaded through original Green loader
    carry set   = ID 0, >151, or high byte nonzero; expanded record path pending

This stage proves a 16-bit API can coexist with the byte-exact legacy runtime
without allocating speculative WRAM/HRAM.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

ROM_SIZE = 0x800000
RUNTIME_BANK = 0x20
RUNTIME_CPU = 0x4000
RUNTIME_FILE_OFFSET = RUNTIME_BANK * 0x4000
RUNTIME_UNSUPPORTED = 0x4038

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
    0: "eaf82fdb16f239fccc49130ff4318c82653f4c457ed03c6c5100f216ef44e922",
    1: "6fd6bf677b8b59e51959244cd4bb454a85665f4cf83ac3ceaecf6e883eff2349",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def global_checksum(data: bytes) -> int:
    return (sum(data[:0x14E]) + sum(data[0x150:])) & 0xFFFF


def runtime_code(legacy_loader: int) -> bytes:
    unsupported = RUNTIME_UNSUPPORTED
    return bytes((
        0x7A,                         # 4000 ld a,d
        0xB7,                         # 4001 or a
        0xC2, unsupported & 0xFF, unsupported >> 8,  # jp nz,unsupported
        0x7B,                         # 4005 ld a,e
        0xB7,                         # 4006 or a
        0xCA, unsupported & 0xFF, unsupported >> 8,  # jp z,unsupported
        0xFE, 0x98,                   # 400A cp 152
        0xD2, unsupported & 0xFF, unsupported >> 8,  # jp nc,unsupported

        0xFA, 0x92, 0xD0,             # 400F ld a,(D092) ; save input species
        0xF5,                         # 4012 push af
        0xFA, 0xE3, 0xD0,             # 4013 ld a,(D0E3) ; save mapping scratch
        0xF5,                         # 4016 push af

        0x7B,                         # 4017 ld a,e ; canonical Gen1 dex
        0xEA, 0xE3, 0xD0,             # 4018 ld (D0E3),a

        0x06, 0x10,                   # 401B ld b,10 ; mapping-table bank
        0x0E, 0x00,                   # 401D ld c,0  ; target bank bit 8
        0x21, 0x6F, 0x67,             # 401F ld hl,676F ; Dex -> internal ID
        0xCD, 0x68, 0x00,             # 4022 call 0068 ; FarCall9FromLow

        0xFA, 0xE3, 0xD0,             # 4025 ld a,(D0E3)
        0xEA, 0x92, 0xD0,             # 4028 ld (D092),a
        0xCD, legacy_loader & 0xFF, legacy_loader >> 8, # call original loader

        0xF1,                         # 402E pop af
        0xEA, 0xE3, 0xD0,             # 402F ld (D0E3),a
        0xF1,                         # 4032 pop af
        0xEA, 0x92, 0xD0,             # 4033 ld (D092),a
        0xB7,                         # 4036 or a ; clear carry
        0xC9,                         # 4037 ret

        0x37,                         # 4038 scf
        0xC9,                         # 4039 ret
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
    if len(code) != 0x3A:
        raise AssertionError("species runtime layout changed")
    if data[RUNTIME_FILE_OFFSET:RUNTIME_FILE_OFFSET + len(code)] != b"\xFF" * len(code):
        raise ValueError("species runtime destination is not empty expansion space")

    out = bytearray(data)
    out[RUNTIME_FILE_OFFSET:RUNTIME_FILE_OFFSET + len(code)] = code

    # Header checksum is unaffected; global checksum covers the whole ROM.
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
        f"GREEN Rev {revision}: installed u16 species runtime at "
        f"bank 0x{RUNTIME_BANK:02X}:0x{RUNTIME_CPU:04X}"
    )
    print(f"sha256={sha256(result)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
