import unittest
import zlib

from tools.expand_green_save import (
    BANK_SIZE,
    EXT_OFFSET,
    MAGIC,
    SOURCE_SIZE as SAVE_SOURCE_SIZE,
    TARGET_SIZE as SAVE_TARGET_SIZE,
    expand_save,
    legacy_checksum,
)
from tools.scan_mapper_writes import positions


class OriginalRomToolTests(unittest.TestCase):
    def make_save(self):
        data = bytearray([0xFF] * SAVE_SOURCE_SIZE)
        for i in range(0x2598, 0x3594):
            data[i] = (i * 13 + 7) & 0xFF
        data[0x3594] = legacy_checksum(bytes(data))
        return bytes(data)

    def test_save_expansion_preserves_legacy_region(self):
        source = self.make_save()
        expanded = expand_save(source, 0)
        self.assertEqual(len(expanded), SAVE_TARGET_SIZE)
        self.assertEqual(expanded[:SAVE_SOURCE_SIZE], source)
        self.assertEqual(expanded[EXT_OFFSET:EXT_OFFSET + 8], MAGIC)
        self.assertEqual(EXT_OFFSET, 4 * BANK_SIZE)

    def test_mapper_write_scan(self):
        blob = b"\x00\xEA\x00\x20\xEA\x00\x30\xEA\x00\x20"
        self.assertEqual(positions(blob, 0x2000), [1, 7])
        self.assertEqual(positions(blob, 0x3000), [4])


if __name__ == "__main__":
    unittest.main()
