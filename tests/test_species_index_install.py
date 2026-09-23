import unittest

from tools.build_u16_far_index import encode_far
from tools.install_species_index import (
    PAGE_DIRECTORY_FILE_OFFSET,
    PAGE_SIZE,
    install_index,
    page_location,
    rom_offset,
)
from tools.patch_species_runtime import ROM_SIZE


class SpeciesIndexInstallTests(unittest.TestCase):
    def test_page_geometry(self):
        self.assertEqual(page_location(0x00), (0x21, 0x4000))
        self.assertEqual(page_location(0x0F), (0x21, 0x7C00))
        self.assertEqual(page_location(0x10), (0x22, 0x4000))
        self.assertEqual(page_location(0xFF), (0x30, 0x7C00))

    def test_install_sparse_entry(self):
        image = bytearray(b"\xFF" * ROM_SIZE)
        result = install_index(
            bytes(image),
            {0x1234: (0x100, 0x4567)},
        )

        page_bank, page_address = page_location(0x12)
        directory = PAGE_DIRECTORY_FILE_OFFSET + 0x12 * 4
        self.assertEqual(
            result[directory:directory + 4],
            encode_far(page_bank, page_address),
        )

        page = rom_offset(page_bank, page_address)
        entry = page + 0x34 * 4
        self.assertEqual(
            result[entry:entry + 4],
            encode_far(0x100, 0x4567),
        )

    def test_legacy_ids_are_rejected(self):
        image = bytes(b"\xFF" * ROM_SIZE)
        with self.assertRaises(ValueError):
            install_index(image, {151: (0x31, 0x4000)})


if __name__ == "__main__":
    unittest.main()
