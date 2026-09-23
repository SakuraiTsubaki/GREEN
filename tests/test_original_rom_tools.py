import unittest

from tools.expand_green_save import (
    EXT_PAYLOAD_OFFSET,
    MAGIC,
    SOURCE_SIZE as SAVE_SOURCE_SIZE,
    TARGET_SIZE as SAVE_TARGET_SIZE,
    build_party_identity_payload,
    expand_save,
    legacy_checksum,
)
from tools.scan_mapper_writes import positions


class OriginalRomToolTests(unittest.TestCase):
    def make_save(self):
        data = bytearray([0xFF] * SAVE_SOURCE_SIZE)
        for i in range(0x2598, 0x3594):
            data[i] = (i * 13 + 7) & 0xFF
        data[0x2ED5] = 1
        data[0x2ED6] = 0x99
        data[0x2ED7] = 0xFF
        data[0x3594] = legacy_checksum(bytes(data))
        return bytes(data)

    def make_species_map(self):
        table = bytearray(190)
        table[0x15 - 1] = 151
        table[0x99 - 1] = 1
        return bytes(table)

    def test_save_expansion_preserves_legacy_region(self):
        source = self.make_save()
        species_map = self.make_species_map()
        expanded = expand_save(source, 0, species_map)
        self.assertEqual(len(expanded), SAVE_TARGET_SIZE)
        self.assertEqual(expanded[:SAVE_SOURCE_SIZE], source)
        self.assertEqual(expanded[0x8000:0x8008], MAGIC)
        self.assertEqual(
            expanded[EXT_PAYLOAD_OFFSET:EXT_PAYLOAD_OFFSET + 4],
            b"\x01\x00\x00\x00",
        )

    def test_party_identity_payload(self):
        payload = build_party_identity_payload(
            self.make_save(),
            self.make_species_map(),
        )
        self.assertEqual(payload[:4], b"\x01\x00\x00\x00")
        self.assertEqual(payload[4:], b"\x00" * 20)

    def test_mapper_write_scan(self):
        blob = b"\x00\xEA\x00\x20\xEA\x00\x30\xEA\x00\x20"
        self.assertEqual(positions(blob, 0x2000), [1, 7])
        self.assertEqual(positions(blob, 0x3000), [4])


if __name__ == "__main__":
    unittest.main()
