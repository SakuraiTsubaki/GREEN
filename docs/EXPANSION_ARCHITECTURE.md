# GREEN Original ROM Expansion Architecture

## 1. Verified source

Both supplied Japanese Green ROMs are 512 KiB and identify cartridge type
0x03 (MBC1 + RAM + battery), ROM size code 0x04, and RAM size code 0x03.
Their header revision bytes are 0 and 1.

The supplied saves are 32 KiB.

## 2. Cartridge expansion target

GREEN expands the original cartridge image to:

- cartridge type 0x1B: MBC5 + RAM + battery;
- ROM size code 0x08: 8 MiB;
- RAM size code 0x04: 128 KiB;
- 512 ROM banks of 16 KiB;
- 16 SRAM banks of 8 KiB.

MBC5 exposes an 8-bit low ROM-bank register at 0x2000-0x2FFF and a ninth ROM
bank bit at 0x3000-0x3FFF. SRAM bank selection remains in 0x4000-0x5FFF.

## 3. Preservation boundary

ROM banks 0x000-0x01F are the original 512 KiB region.

The ROM expansion tool copies this region unchanged except the cartridge header
fields required for mapper/size migration and the two checksums that cover the
header/image.

Banks 0x020-0x1FF are new expansion space.

SRAM banks 0x00-0x03 are copied byte-for-byte from the original 32 KiB save.
Banks 0x04-0x0F are expansion space.

## 4. Mapper migration evidence

A direct opcode scan of both supplied ROM revisions found identical exact
absolute-store patterns:

- `LD (0x2000),A`: 89 occurrences;
- `LD (0x3000),A`: 0 occurrences;
- `LD (0x4000),A`: 19 occurrences;
- `LD (0x6000),A`: 25 occurrences.

This is a byte-pattern census, not proof that every hit is executable code.
Each bank-switching path still requires control-flow verification before new
banks above 0x1F are used.

The absence of exact 0x3000 writes is useful: the original image does not
already appear to manipulate MBC5's ninth ROM-bank register through that exact
instruction pattern.

## 5. Expanded bank ABI

New code/data uses an explicit far reference:

- bank: 16-bit storage, valid 0x000-0x1FF;
- CPU address: 16-bit, normally 0x4000-0x7FFF for switchable ROM;
- total stored size: 4 bytes.

Using four bytes avoids a future second migration when bank 0x100-0x1FF is used.

## 6. Content IDs

Legacy Green species/move/item IDs remain 8-bit source values. Expanded tables
do not use those bytes as a global namespace.

GREEN reserves 16-bit IDs for species, forms, moves, items, abilities, types,
locations, maps, trainer classes, and evolution methods.

## 7. Save extension

The original four SRAM banks remain the legacy save area.

Expansion bank 0x04 begins with a versioned GREEN extension header. New
Generation-10-ready records live in banks 0x04-0x0F and reference content using
the widened IDs.

No sample all-0xFF byte in the original four banks is treated as guaranteed
free capacity.

## 8. Build rule

ROM/SAV binaries are generated locally from user-supplied inputs and are never
committed. CI validates tools, manifests, and tests without downloading or
building any external engine.
