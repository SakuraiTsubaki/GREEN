# MBC5 banking implementation

GREEN resumes from the original Japanese Green ROM, not a replacement engine.

## Verified legacy bank core

The supplied Rev 0 and Rev A images contain the same bank-switch structure at
revision-shifted addresses.

| Role | Rev 0 | Rev A |
| --- | ---: | ---: |
| temporary switch | 0x3606 | 0x35F4 |
| restore saved bank | 0x3617 | 0x3605 |
| 8-bit far-call | 0x3620 | 0x360E |

The far-call core saves the current low bank from HRAM 0xFFB8, switches to the
bank in B, jumps to HL, and restores the old bank after the callee returns.

Exact direct opcode references to the far-call entry number 264 in each
revision. The routine is therefore a primary compatibility boundary.

## Why the old routine is kept

Legacy Green only needs banks 1-31. Rewriting hundreds of legacy callers before
the new bank space is used would add unnecessary risk.

MBC5 accepts the old low-bank write at 0x2000. The new ninth bank bit is kept
zero whenever legacy code is active.

The existing 8-bit far-call therefore remains the legacy path.

## Fixed 9-bit bridge

GREEN installs a new bridge in fixed ROM bank 0 at 0x0068-0x009A.

The current recursive fixed-bank analysis does not execute this range in either
verified revision. No verified fixed-bank direct CALL/JP targets it.

### Calling convention

For a target bank 0x000-0x1FF:

- B = low 8 bits of target bank;
- C bit 0 = target bank bit 8;
- HL = target CPU address in 0x4000-0x7FFF.

Use:

- CALL 0x0068 when the **caller** bank is 0x000-0x0FF;
- CALL 0x006D when the **caller** bank is 0x100-0x1FF.

The two entries choose different return trampolines. This lets nested calls
restore the caller's ninth bank bit without allocating an unverified WRAM/HRAM
byte.

## Boot initialization

The cartridge entry point is redirected to 0x0094.

That stub writes zero to MBC5 register 0x3000 and then jumps to the original
Green entry at 0x0150. Legacy execution therefore begins with bank bit 8 clear.

## Original RAM banking

Verified save-related code uses the MBC1 control pattern:

- RAM enable write at 0x0000;
- mode select at 0x6000;
- RAM bank at 0x4000.

Under MBC5, 0x6000 is not a banking register while 0x4000-0x5FFF directly
selects RAM bank. The legacy 0/1 RAM-bank writes observed in Green remain valid
for the original four-bank save area.

The new save extension uses banks 0x04-0x0F.

## Remaining migration work

The bridge makes all 512 ROM banks addressable. It does **not** by itself widen
every Generation I data table.

Next migrations proceed domain by domain:

1. species/form identity and species-table lookup;
2. move identity and move-table lookup;
3. item identity and inventory/storage records;
4. evolution/learnset references;
5. trainer and encounter records;
6. script/data far pointers;
7. expanded persistent Pokémon/save records.

Each domain keeps original byte IDs as a compatibility namespace and adds an
explicit 16-bit expanded namespace.
