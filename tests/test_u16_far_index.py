import unittest

from tools.build_u16_far_index import (
    EMPTY,
    ENTRY_SIZE,
    ENTRIES_PER_PAGE,
    PAGE_SIZE,
    build_pages,
    encode_far,
)


class U16FarIndexTests(unittest.TestCase):
    def test_far_pointer_supports_last_mbc5_bank(self):
        encoded = encode_far(0x1FF, 0x7FFF)
        self.assertEqual(encoded, b"\xFF\x01\xFF\x7F")

    def test_sparse_pages(self):
        pages = build_pages({
            0x0001: (0x20, 0x4000),
            0x0102: (0x100, 0x4567),
        })
        self.assertEqual(set(pages), {0x00, 0x01})
        self.assertEqual(len(pages[0]), PAGE_SIZE)
        self.assertEqual(len(pages[1]), PAGE_SIZE)
        self.assertEqual(
            pages[0][ENTRY_SIZE:ENTRY_SIZE * 2],
            encode_far(0x20, 0x4000),
        )
        start = 0x02 * ENTRY_SIZE
        self.assertEqual(
            pages[1][start:start + ENTRY_SIZE],
            encode_far(0x100, 0x4567),
        )
        self.assertEqual(pages[0][0:ENTRY_SIZE], EMPTY)

    def test_page_geometry(self):
        self.assertEqual(ENTRIES_PER_PAGE, 256)
        self.assertEqual(PAGE_SIZE, 1024)


if __name__ == "__main__":
    unittest.main()
