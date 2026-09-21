# GREEN Save Schema Contract

GREEN uses a versioned remake save schema and a separate importer for original
Pocket Monsters Green save images.

## Evidence boundary

The supplied Rev 0 and Rev A save snapshots are both exactly 32 KiB, matching
four 8 KiB SRAM banks reported by the ROM cartridge header.

In both supplied snapshots, banks 2 and 3 are entirely 0xFF. This is **not**
treated as guaranteed free space. A pair of snapshots cannot prove that a bank
is unused by every game state, subsystem, or revision.

The two snapshots differ by 993 bytes. Because they were saved independently,
those bytes cannot be labelled revision-format differences without controlled
experiments.

See `docs/ROM_SAVE_EVIDENCE.md`.

## Legacy importer

Original Green saves are accepted as a 32 KiB source format. The importer must:

- retain the source ROM revision and source save hash as provenance;
- parse legacy fields without widening them in place;
- map legacy species/item/move IDs to canonical GREEN IDs;
- validate known checksums once their exact ranges are verified;
- preserve unknown bytes until their purpose is established.

## Expanded save

Every expanded GREEN save identifies:

- save format version;
- data/schema version;
- enabled feature flags;
- integrity/checksum information;
- migration source when converted from an older schema.

The project reserves 16 bits for the format version, 16 bits for the schema
version, and 64 bits for feature flags.

Persistent Pokémon records use the widths from `config/capacity.json`.
Species and form are separate identities. Temporary battle-only forms are not
serialized as permanent species identities unless a mechanic explicitly
requires persistent state.

## Migration

Save compatibility is handled by explicit deterministic migrations:

`vN -> vN+1`

Original Pocket Monsters Green saves are import sources, not `v0` of the new
layout. New mechanics use versioned extension blocks rather than undocumented
padding or bytes that merely appear unused in sample saves.
