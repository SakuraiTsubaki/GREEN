# GREEN engine patches

These patches target the pinned modern core:

`rh-hideout/pokeemerald-expansion@75b806a3ab57a81ff1eb6179288981f0b3cc3050`

They are kept outside the upstream checkout so GREEN can audit every engine
change independently.

Current order:

1. `0001-green-expand-persistent-species-item-ids.patch`
   - widens persistent species/form and held-item storage to 16 bits;
   - keeps `PokemonSubstruct0` at 12 bytes;
   - adds compile-time capacity guards, including the current 11-bit move gate.
2. `0002-green-runtime-identity.patch`
   - selects the LeafGreen/Kanto runtime;
   - assigns Japanese GREEN development-build identity;
   - does not claim an official Nintendo/Game Freak product code.

Apply only to the pinned commit and validate with
`tools/prepare_green_engine.py`.
