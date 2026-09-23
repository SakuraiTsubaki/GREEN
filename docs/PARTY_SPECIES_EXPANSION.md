# Party species persistence expansion

## Verified party block

Both supplied ROM revisions use the same SRAM/WRAM party copy geometry.

During load, code in ROM bank 0x1C copies:

- source SRAM 0xAED5
- destination WRAM 0xD123
- length 0x0158

During save it copies the same 0x0158 bytes in the opposite direction.

This maps to save-file offset 0x2ED5 because 0xAED5 is in SRAM bank 1.

The 344-byte block decomposes exactly as:

- 1 byte party count;
- 7-byte party species list;
- 6 x 44-byte party-mon records;
- 6 x 6-byte Japanese OT-name slots;
- 6 x 6-byte Japanese nickname slots.

The next region begins at save offset 0x302D / WRAM 0xD27B.

## Actual supplied saves

Both current save snapshots contain:

- party count = 1;
- first species-list internal ID = 0x99;
- first 44-byte party-mon species byte = 0x99.

## Internal ID mapping

ROM bank 0x10 at CPU 0x679A / file offset 0x4279A contains a 190-byte
internal-species -> National Pokédex table.

It is byte-identical in Rev 0 and Rev A.

Verified examples:

- internal 0x15 -> National Dex 151 (Mew);
- internal 0x99 -> National Dex 1 (Bulbasaur).

The mapping contains 39 zero entries corresponding to internal slots that do
not map to a normal Pokédex species.

Code immediately before the table provides both directions:

- 0x676F searches the table to convert a Pokédex number to an internal ID;
- 0x6786 indexes the table to convert an internal ID to a Pokédex number.

The base-stat loader's observed predef 0x3A path is therefore tied to this
legacy mapping layer.

## Expanded save sidecar

GREEN keeps the original first 32 KiB byte-exact.

Expansion SRAM bank 0x04 local offset 0x0020 stores six party identity entries.
Each is:

- u16 species_id;
- u16 form_id.

For Generation I migration, canonical base species IDs use the verified
National Pokédex number. Forms start at 0.

An occupied legacy internal slot with no Pokédex mapping becomes 0xFFFF rather
than being silently reinterpreted.

This sidecar is already produced by `tools/expand_green_save.py` from the
paired verified ROM and save.

## Next runtime seam

Persistence now has a 16-bit party identity, but the live legacy party block
still contains one-byte species fields.

The next runtime patch must add a current expanded identity context and route
the base-stat loader through the new 16-bit species index when that context is
non-zero, while leaving original party/box behavior byte-compatible.
