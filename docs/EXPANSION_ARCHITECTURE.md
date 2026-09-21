# GREEN Expansion Architecture

## Goal

GREEN is expanded **before** Generation I content is ported. The purpose is to
avoid rebuilding the engine whenever later-generation data is introduced.

The design target is Generation-10-ready capacity. This does **not** guess or
assign unreleased Generation 10 species, moves, items, abilities, forms, or
mechanics. Future content is loaded through tables and manifests.

## 1. ID model

The original game uses compact IDs suited to its 1996 content set. Those IDs
remain part of the compatibility layer only.

Expanded runtime IDs:

| Domain | Storage | Rule |
| --- | ---: | --- |
| Species | u16 | Base species identity only |
| Form | u16 | Separate from species |
| Move | u16 | No 8-bit global ceiling |
| Item | u16 | No 8-bit global ceiling |
| Ability | u16 | Added by the remake layer |
| Type | u8 | 0-254 usable; 255 reserved |
| Location | u16 | Stable logical location ID |
| Map | u16 | Stable logical map ID |
| Trainer class | u16 | Data-driven |
| Evolution method | u16 | Extensible condition namespace |

`0xFFFF` is reserved as an invalid u16 ID and must not become real content.

## 2. Species and forms

Do not encode every form as an unrelated species slot.

A Pokémon identity is modeled as:

- `species_id`: persistent base species identity;
- `form_id`: persistent or selected form identity;
- `battle_form_id`: temporary battle-only state when applicable;
- optional form parameters for mechanics that require additional state.

This allows regional forms, cosmetic forms, battle-only forms, item-driven
forms, weather forms, stance forms, and future mechanics without exhausting the
species namespace or changing save structure again.

## 3. Original Green compatibility

Original Green IDs are imported through explicit mapping tables:

`original_id -> expanded_id`

Never reinterpret an original byte ID as if it were the new global ID. This
keeps byte-exact source research separate from remake runtime representation.

## 4. Data tables

Species, forms, moves, items, abilities, evolution rules, learnsets, encounters,
trainers, maps, text, graphics, and mechanics must be addressable through
generated tables or manifests.

Engine code may depend on table contracts, but must not depend on the current
highest National Pokédex number or current move/item count.

## 5. Capacity policy

The configured widths are architectural ceilings, not allocation targets.
Memory and ROM should still be banked/segmented so only required data is loaded
at runtime.

Large datasets must support:

- generated index tables;
- segmented/banked storage;
- pointer or offset tables wider than legacy byte indices where needed;
- compile-time validation of every reference;
- stable IDs independent of physical storage order.

## 6. Mechanics

Later-generation mechanics are feature modules. A mechanic must declare:

- persistent state, if any;
- battle-only state, if any;
- required data tables;
- save migration impact;
- compatibility behavior when disabled.

This prevents Mega Evolution, regional mechanics, form changes, or future
mechanics from being hard-wired into the base species table.

## 7. Generation 10 rule

When official Generation 10 data becomes available, GREEN should require data
and feature-module additions, not another widening of species/move/item IDs or a
new save identity model.

If a future feature exceeds a declared storage width, the capacity schema must
be revised explicitly with a migration path rather than silently truncating
data.
