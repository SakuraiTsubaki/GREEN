# Species ID expansion

## ROM evidence

GREEN's original species data is not a single 151-entry modern-style table.

### Ordinary species

Both verified revisions have a 28-byte base-stat table beginning at:

- ROM bank 0x0E
- CPU address 0x4000
- file offset 0x38000

The first byte of each record is the National Pokédex number. Records 1 through
150 are sequential and occupy 150 x 28 = 4200 bytes.

The complete 150-record region is byte-identical between Rev 0 and Rev A.

### Mew

Mew is not the 151st record in that bank-0x0E table.

Its 28-byte record is separately stored at:

- ROM bank 0x01
- CPU address 0x4200
- file offset 0x04200

Its first bytes are:

`97 64 64 64 64 64 18 18 ...`

which encode Pokédex 151 and the original 100/100/100/100/100 Gen I stat line.

The record is byte-identical in both supplied revisions.

## Loader evidence

The base-stat loader begins at:

- Rev 0: 0x2F2E
- Rev A: 0x2F1C

There are 29 exact direct CALL references to the corresponding entry in each
ROM.

The routine saves the current ROM bank, selects bank 0x0E, and reads the
working species byte at 0xD0E3.

Internal species value 0x15 takes the separate Mew path at bank 0x01:0x4200.

The ordinary path invokes predef ID 0x3A, then reads 0xD0E3 again, subtracts
one, multiplies it by 28, adds it to 0x4000, and copies one 28-byte record.

This proves that the current execution boundary is an **8-bit internal species
identity feeding a fixed-size lookup**, not simply a 151-record array that can
be extended in place.

## GREEN expansion boundary

Original species continue using the original loader while it is being
preserved and verified.

Expanded species use:

- 16-bit species ID;
- separate 16-bit form ID;
- explicit legacy-internal-ID -> canonical-ID mapping;
- a sparse paged 16-bit index;
- 4-byte MBC5 far pointers.

The index splits an ID as:

`HHLL -> page HH -> slot LL`

An allocated page is 256 x 4 = 1024 bytes. Unused high-byte pages consume no
ROM.

This keeps the full 16-bit namespace available without allocating a 256 KiB
flat pointer table up front.

## Why the 28-byte table is not widened in place

The legacy record has one Special stat and Generation I-specific fields. Modern
content needs data that did not exist in this format, including separate
Special Attack/Special Defense and later mechanic metadata.

GREEN therefore preserves the legacy record for original compatibility and
places modern records in expansion banks. The new 16-bit dispatch layer chooses
which representation to load.

The next binary patch is the dispatcher at the species-loader boundary. Before
installing it, GREEN must allocate the runtime high byte/form state and verify
every party/battle/save path that currently assumes the one-byte species
identity.
