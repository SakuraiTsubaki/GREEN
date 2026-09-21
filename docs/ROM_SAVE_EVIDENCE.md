# Pocket Monsters Green ROM / save evidence

This document records observations from the two supplied Japanese Green ROMs
and the two save snapshots. The ROM and save binaries themselves are not stored
in this repository.

## Verified ROM baseline

Both ROMs are exactly 524,288 bytes (512 KiB), which is 32 x 16 KiB ROM banks.

Observed cartridge header fields are identical except for revision/checksum data:

| Field | Rev 0 | Rev A |
| --- | --- | --- |
| Title | POKEMON GREEN | POKEMON GREEN |
| SGB flag | 0x03 | 0x03 |
| Cartridge type | 0x03 | 0x03 |
| ROM size code | 0x04 | 0x04 |
| RAM size code | 0x03 | 0x03 |
| Header revision | 0 | 1 |
| Header checksum | 0x9C | 0x9B |
| Global checksum | 0xDDD5 | 0xF547 |

Cartridge type 0x03 is the legacy Green compatibility target represented by the
input: MBC1 + RAM + battery. RAM size code 0x03 corresponds to the 32 KiB save
files supplied with the ROMs.

Both header checksum and global checksum validate against the supplied bytes.

## Revision difference is not a header-only patch

The two ROM images differ in **46,168 bytes** across **5,436 contiguous change
ranges**.

31 of 32 ROM banks contain at least one changed byte. Bank 27 is identical in
the supplied images. Banks 0, 1, and 15 contain the largest changes.

Therefore GREEN must treat Rev 0 and Rev A as two independently verified source
baselines. A remake importer must not assume that revision handling can be
reduced to changing header byte 0x014C.

See `analysis/rom-bank-diff.csv` for per-bank counts.

## Verified save snapshots

Both save files are exactly 32,768 bytes, matching four 8 KiB SRAM banks.

Observed snapshot occupancy:

- bank 0: data is present through local offset 0x0497;
- bank 1: data is present through local offset 0x1594;
- bank 2: every byte is 0xFF in both supplied snapshots;
- bank 3: every byte is 0xFF in both supplied snapshots.

The two snapshots differ in **993 bytes**:

- bank 0: 950 differing bytes;
- bank 1: 43 differing bytes;
- banks 2 and 3: 0 differing bytes.

These saves were produced independently from different ROM revisions, so the
993-byte difference is **not** classified as a revision-format difference.
Gameplay state and initialization state can also change save bytes.

Likewise, banks 2 and 3 being all 0xFF in these two snapshots is observation,
not proof that those banks are universally unused or safe expansion space.

## Expansion consequence

The original ROM/save pair is an **input compatibility format**, not the storage
model for Generation-10-ready GREEN.

GREEN therefore uses two layers:

1. **Legacy Green adapter**
   - accepts a byte-exact 512 KiB Rev 0 or Rev A ROM identity;
   - accepts a byte-exact 32 KiB legacy save image;
   - preserves banked source offsets and revision provenance;
   - maps original IDs and save fields into canonical remake IDs/state.

2. **Expanded GREEN runtime**
   - does not reuse apparent blank bytes in a sample save as a capacity plan;
   - does not inherit the original 8-bit content ceilings;
   - keeps species and form identities separate;
   - uses versioned save schemas and explicit migrations;
   - keeps physical storage order separate from stable logical IDs.

Any later claim about a specific legacy save field, checksum, unused range, or
revision-specific structure must be backed by additional ROM access analysis or
controlled save experiments.
