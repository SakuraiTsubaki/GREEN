import unittest

from src.source_formats.gen1_green import (
    CARTRIDGE_SRAM_SIZE,
    JAPANESE_GREEN_SAVE,
    MAIN_DATA_START,
    ROM_SIZE,
    checksum_valid,
    normalize_raw_save,
    require_green_save,
    rby_checksum,
)


class Gen1GreenSourceFormatTests(unittest.TestCase):
    def make_save(self):
        data = bytearray([0xFF] * CARTRIDGE_SRAM_SIZE)
        for i in range(MAIN_DATA_START, JAPANESE_GREEN_SAVE.checksum_offset):
            data[i] = (i * 17 + 3) & 0xFF
        data[JAPANESE_GREEN_SAVE.checksum_offset] = rby_checksum(bytes(data))
        return bytes(data)

    def test_verified_japanese_layout(self):
        data = self.make_save()
        self.assertTrue(checksum_valid(data))
        self.assertEqual(require_green_save(data).key, "japanese-green")
        self.assertEqual(JAPANESE_GREEN_SAVE.box_count, 8)
        self.assertEqual(JAPANESE_GREEN_SAVE.box_slots, 30)

    def test_normalize_emulator_footer(self):
        core = bytes([0xFF]) * CARTRIDGE_SRAM_SIZE
        normalized, tail = normalize_raw_save(core + b"footer")
        self.assertEqual(normalized, core)
        self.assertEqual(tail, b"footer")

    def test_rom_capacity_constant(self):
        self.assertEqual(ROM_SIZE, 512 * 1024)


if __name__ == "__main__":
    unittest.main()
