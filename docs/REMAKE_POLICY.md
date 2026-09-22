# GREEN Original-ROM Expansion Policy

## Runtime boundary

GREEN runs as a **Game Boy / Super Game Boy ROM** derived from the original
Japanese Pocket Monsters Green ROM.

Do not substitute a GBA, Generation III, or other external engine as GREEN's
runtime.

## Preserve

- original Japanese Rev 0 / Rev A provenance;
- original maps, scripts, events, battle logic, text, graphics, audio, and save
  behavior until a specific expansion change is intentionally implemented;
- original 512 KiB ROM content by bank;
- original 32 KiB save content during migration.

## Expand

The cartridge target is MBC5 + RAM + battery so GREEN can address up to 8 MiB
of ROM and 128 KiB of SRAM while remaining a Game Boy cartridge architecture.

New systems use widened project IDs and banked tables instead of assuming the
Generation I byte-sized maxima.

## Generation 10

Capacity is prepared now; unreleased data is not guessed.

Future official content should be addable as new banked data and code without
another global ID-width migration.
