# Expanded species index runtime

## Resolver result contract

GREEN's species resolver lives at bank 0x20:$4000 and takes a canonical
16-bit species ID in DE.

It returns one of three states:

- **carry clear, A=0** — IDs 1-151 were translated through the verified
  Generation I internal-ID table and loaded with the original Green base-stat
  loader. The legacy work buffer at D095 is ready.
- **carry clear, A=1** — an expanded record was found. BC contains the
  little-endian 9-bit-capable ROM bank value and DE contains its CPU address.
- **carry set** — zero ID or no record is installed.

No new global RAM variable is needed for the high species byte.

## Page directory

Bank 0x20:$4100 contains 256 four-byte directory entries, one for each possible
high byte of a u16 species ID.

An entry is:

- u16 ROM bank;
- u16 CPU address.

0xFFFFFFFF means the page is absent.

## Deterministic page region

The full index page surface is reserved in banks 0x21-0x30.

Each 1 KiB page holds 256 record far pointers. Page HH is located at:

- bank = 0x21 + HH / 16;
- address = 0x4000 + (HH mod 16) * 0x0400.

Thus the complete 65536-ID namespace needs at most sixteen 16 KiB banks for
indexing. Sparse builds only write pages that contain entries.

Species records start at bank 0x31 or later.

## Fixed-bank data reader

A helper at $009B reads four bytes from any 9-bit MBC5 bank while code continues
executing in fixed bank 0. It restores bank 0x20 after each lookup.

This is why page and record pointers can address banks through 0x1FF without
allocating a new bank-state byte in WRAM or HRAM.

## Record core

Expanded records begin with the versioned 48-byte `SpeciesCoreV1` defined by
`config/species-record-v1.json`.

The core intentionally separates:

- species ID and form ID;
- six modern base stats;
- type IDs;
- ability IDs;
- growth/catch/breeding metadata;
- EV yields;
- an optional far pointer to versioned extension data.

The schema defines capacity only. It does not invent Generation 10 content.

## Next migration

With ROM banking, save persistence, 16-bit species entry, and expanded record
lookup now separated cleanly, the next runtime migration is to move concrete
consumers away from assuming that every species is represented by the legacy
28-byte D095 buffer.

Battle stat initialization is the first high-value consumer to split into
legacy and expanded-record paths.
