# GREEN Project

## Canonical direction

GREEN is an **original Game Boy ROM expansion project** for Japanese
`ポケットモンスター 緑`.

The project does not use a GBA runtime. The supplied Japanese Green Rev 0 and
Rev A ROMs and their save files are the executable/storage baseline.

## Source baselines

- Pocket Monsters Green Rev 0 (Japan)
- Pocket Monsters Green Rev A (Japan)
- one 32 KiB save snapshot for each revision

ROM binaries and save binaries remain outside Git. Hashes and reproducible
observations are committed.

## Expansion target

The original cartridge profile is:

- MBC1 + RAM + battery
- 512 KiB ROM (32 x 16 KiB banks)
- 32 KiB SRAM (4 x 8 KiB banks)

GREEN's Generation-10-ready storage target is still a Game Boy cartridge image:

- MBC5 + RAM + battery
- up to 8 MiB ROM (512 x 16 KiB banks)
- up to 128 KiB SRAM (16 x 8 KiB banks)
- Super Game Boy flag preserved
- first 512 KiB of ROM preserved except required cartridge-header fields/checksums
- first 32 KiB of save data preserved byte-for-byte during migration

The mapper transition and every bank-switching callsite are verified against
the original ROM before expanded banks become runtime dependencies.

## Data-width rule

Legacy byte IDs remain source IDs. Expanded content uses project IDs wide
enough for future official content:

- species: 16-bit
- form: 16-bit
- move: 16-bit
- item: 16-bit
- ability: 16-bit
- type: 16-bit
- logical map/location/trainer/evolution IDs: 16-bit

ROM far references use a 9-bit-capable bank field plus a 16-bit CPU address.

No unreleased Generation 10 species, moves, items, forms, abilities, or
mechanics are fabricated.
