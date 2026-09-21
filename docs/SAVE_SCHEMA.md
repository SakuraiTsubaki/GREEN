# GREEN Save Schema Contract

GREEN save data is versioned from the beginning because the remake runtime is
not constrained to the original Generation I entity layout.

## Required metadata

Every expanded save format must identify:

- save format version;
- data/schema version;
- enabled feature flags;
- integrity/checksum information;
- migration source when converted from an older schema.

The project reserves 16 bits for the format version, 16 bits for the data
schema version, and 64 bits for feature flags.

## ID storage

Expanded save blocks use the widths from `config/capacity.json`.

In particular, persistent Pokémon records must not store the global species,
move, item, ability, or form identities in legacy 8-bit fields.

Base species and form are separate fields. Temporary battle-only forms are not
serialized as permanent species identities unless a mechanic explicitly
requires persistent state.

## Migration

Save compatibility is handled by explicit migrations:

`vN -> vN+1`

A migration must be deterministic and testable. Old fields are never silently
reinterpreted with a new meaning.

Original Pocket Monsters Green save data, when supported, is treated as an
import source format and converted into the expanded GREEN schema.

## Future generations

New generations may add fields through versioned extension blocks. Unknown
future mechanics must not consume undocumented padding bytes or rely on current
table sizes.
