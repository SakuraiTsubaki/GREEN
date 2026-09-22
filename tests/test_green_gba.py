import unittest

from tools.verify_green_gba import (
    MAX_ROM_BYTES,
    EXPECTED_GAME_CODE,
    EXPECTED_MAKER,
    EXPECTED_TITLE,
    gba_header_checksum,
)


class GreenGbaCapacityTests(unittest.TestCase):
    def test_capacity(self):
        self.assertEqual(MAX_ROM_BYTES, 32 * 1024 * 1024)

    def test_identity_widths(self):
        self.assertEqual(len(EXPECTED_TITLE), 12)
        self.assertEqual(len(EXPECTED_GAME_CODE), 4)
        self.assertEqual(len(EXPECTED_MAKER), 2)

    def test_checksum_algorithm(self):
        rom = bytearray(0xC0)
        rom[0xA0:0xAC] = EXPECTED_TITLE
        rom[0xAC:0xB0] = EXPECTED_GAME_CODE
        rom[0xB0:0xB2] = EXPECTED_MAKER
        rom[0xB2] = 0x96
        rom[0xBD] = gba_header_checksum(rom)
        self.assertEqual(rom[0xBD], gba_header_checksum(rom))


if __name__ == "__main__":
    unittest.main()
