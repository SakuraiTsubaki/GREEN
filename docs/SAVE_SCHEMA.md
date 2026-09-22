# GREEN Expanded Save Schema

## Source

Japanese Green uses a 32 KiB battery-backed save image (four 8 KiB SRAM banks).

The supplied Rev 0 and Rev A snapshots validate against the Japanese Gen I main
checksum currently recorded by GREEN.

## Target

The original-ROM expansion target uses MBC5 with 128 KiB SRAM (sixteen 8 KiB
banks).

### Banks 0x00-0x03

Legacy Green area. A migration copies all 32 KiB byte-for-byte. Existing Green
code continues to see its original data.

### Banks 0x04-0x0F

GREEN extension area.

Bank 0x04 starts with this little-endian header:

| Offset | Size | Field |
| --- | ---: | --- |
| 0x0000 | 8 | ASCII magic `GRN10EXT` |
| 0x0008 | 2 | schema version |
| 0x000A | 1 | source ROM revision |
| 0x000B | 1 | flags |
| 0x000C | 4 | extension payload length |
| 0x0010 | 4 | payload CRC32 |
| 0x0014 | 4 | reserved |

Initial schema version is 1.

The remainder of the expanded save is initialized to 0xFF until an expanded
system owns a range.

## ID rule

New persistent records use 16-bit IDs for species, form, move, item, ability,
type, and other globally extensible content domains.

The existing first 32 KiB is not widened in place. Compatibility data is
translated when an expanded subsystem reads or migrates a legacy record.
