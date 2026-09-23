# Species ID expansion

## Corrected live identity boundary

The verified base-stat loader does **not** take its species from 0xD0E3.

Its input internal species byte is **0xD092**.

The loader saves the previous value of 0xD0E3, copies 0xD092 into 0xD0E3, uses
0xD0E3 as the internal-ID/Pokédex conversion scratch byte, loads a 28-byte base
stat record into **0xD095**, overwrites the first byte at 0xD095 with the
original internal species ID from 0xD092, and restores 0xD0E3.

Verified loader entries:

- Rev 0: 0x2F2E
- Rev A: 0x2F1C

Each has 29 exact direct CALL references.

This correction matters because GREEN must not allocate a speculative “species
high byte” next to the wrong legacy variable.

## Internal species mapping

ROM bank 0x10 contains the 190-byte internal-ID mapping table at 0x679A
(file offset 0x4279A).

Two routines immediately precede it:

- 0x676F: National Pokédex number in 0xD0E3 -> legacy internal ID in 0xD0E3;
- 0x6786: legacy internal ID in 0xD0E3 -> National Pokédex number in 0xD0E3.

The table is identical in Rev 0 and Rev A.

Examples:

- internal 0x15 -> National Dex 151;
- internal 0x99 -> National Dex 1.

## Base-stat storage

Ordinary species 1-150 use 28-byte records at bank 0x0E:0x4000
(file 0x38000).

Mew is separate at bank 0x01:0x4200.

The ordinary 150-record region and the Mew record are byte-identical between the
two verified revisions.

## First actual 16-bit runtime entry

GREEN now reserves expansion bank 0x20:0x4000 for the first species runtime API.

The API takes:

`DE = canonical u16 species_id`

For IDs 1-151:

1. it saves the current legacy 0xD092 and 0xD0E3 values on the CPU stack;
2. writes the low canonical ID to 0xD0E3;
3. calls the original bank-0x10 routine at 0x676F through the new 9-bit MBC5
   far-call bridge, converting Pokédex number to internal ID;
4. places the internal ID in 0xD092;
5. calls the revision-correct original base-stat loader;
6. restores both legacy variables;
7. returns carry clear.

No new WRAM or HRAM byte is consumed.

ID 0 or any ID above 151 currently returns carry set. That result is the
explicit seam for the next implementation step: modern expansion records.

The runtime bytes are installed by `tools/patch_species_runtime.py`.

## 16-bit expanded lookup

Expanded records use a sparse paged index:

`HHLL -> page HH -> slot LL`

Each allocated page has 256 four-byte MBC5 far pointers:

- little-endian u16 ROM bank;
- little-endian u16 CPU address.

A page is 1024 bytes and only used pages consume ROM space. This preserves the
full 16-bit namespace without preallocating a flat 256 KiB pointer table.

## Next binary step

The next step is to define the modern expansion species record and implement the
carry-set branch for IDs above 151. That branch will load from the paged far
index instead of forcing later-generation fields into the Generation I
28-byte record.
