import unittest

from tools.expand_green_rom import (
    BRIDGE_END,
    BRIDGE_HIGH_ENTRY,
    BRIDGE_LOW_ENTRY,
    BRIDGE_RETURN_HIGH,
    BRIDGE_RETURN_LOW,
    BRIDGE_RESTORE,
    MBC5_BRIDGE,
    MBC5_INIT,
    MBC5_INIT_BYTES,
    MBC5_INIT_END,
    NEW_ENTRY,
    TARGET_SIZE,
    install_mbc5_bridge,
)


class Mbc5BridgeTests(unittest.TestCase):
    def test_layout_addresses(self):
        self.assertEqual(BRIDGE_LOW_ENTRY, 0x0068)
        self.assertEqual(BRIDGE_HIGH_ENTRY, 0x006D)
        self.assertEqual(BRIDGE_RETURN_LOW, 0x0081)
        self.assertEqual(BRIDGE_RETURN_HIGH, 0x0087)
        self.assertEqual(BRIDGE_RESTORE, 0x008C)
        self.assertEqual(BRIDGE_END, 0x0094)
        self.assertEqual(MBC5_INIT, 0x0094)
        self.assertEqual(MBC5_INIT_END, 0x009B)

    def test_bridge_uses_both_mbc5_rom_bank_registers(self):
        self.assertIn(bytes((0xEA, 0x00, 0x20)), MBC5_BRIDGE)
        self.assertIn(bytes((0xEA, 0x00, 0x30)), MBC5_BRIDGE)

    def test_bridge_installs_without_growth(self):
        image = bytearray([0xFF]) * TARGET_SIZE
        install_mbc5_bridge(image)
        self.assertEqual(
            image[BRIDGE_LOW_ENTRY:BRIDGE_END],
            MBC5_BRIDGE,
        )
        self.assertEqual(image[MBC5_INIT:MBC5_INIT_END], MBC5_INIT_BYTES)
        self.assertEqual(image[0x100:0x104], NEW_ENTRY)


if __name__ == "__main__":
    unittest.main()
