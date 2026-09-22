# GREEN

Japanese **ポケットモンスター 緑** expanded from its **original Game Boy ROM**.

GREEN does not move the game to GBA. The executable baseline is the supplied
Japanese Green Rev 0 / Rev A Game Boy ROM pair.

## Current expansion target

- source: MBC1, 512 KiB ROM, 32 KiB SRAM
- target: **MBC5, 8 MiB ROM, 128 KiB SRAM**
- source ROM banks 0x00-0x1F preserved
- source SRAM banks 0x00-0x03 preserved
- new ROM banks 0x20-0x1FF reserved for expanded code/data
- new SRAM banks 0x04-0x0F reserved for versioned expansion data
- global content IDs are widened to 16-bit

The target is capacity for Generation 10 without inventing unreleased content.

## Evidence and tools

- `research/green-baselines.csv` — verified input hashes
- `analysis/rom-bank-diff.csv` — Rev 0 / Rev A bank differences
- `analysis/save-bank-observations.csv` — supplied save observations
- `analysis/mapper-write-summary.csv` — direct mapper-write opcode scan
- `tools/inspect_green_inputs.py` — baseline inspection
- `tools/scan_mapper_writes.py` — mapper write census
- `tools/expand_green_rom.py` — 512 KiB MBC1 -> 8 MiB MBC5 image scaffold
- `tools/expand_green_save.py` — 32 KiB -> 128 KiB save migration scaffold

ROM/SAV binaries are never committed.
