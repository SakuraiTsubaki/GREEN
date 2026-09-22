from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class GreenExpansionTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(
            (ROOT / "config/capacity.json").read_text(encoding="utf-8")
        )

    def test_original_rom_runtime(self):
        self.assertEqual(self.data["runtime"], "original-game-boy-rom")
        self.assertIn("no-gba-engine-dependency", self.data["invariants"])

    def test_mapper_capacity(self):
        self.assertEqual(self.data["source"]["mapper"], "MBC1+RAM+BATTERY")
        self.assertEqual(self.data["expanded"]["mapper"], "MBC5+RAM+BATTERY")
        self.assertEqual(self.data["expanded"]["rom_bytes"], 8 * 1024 * 1024)
        self.assertEqual(self.data["expanded"]["rom_banks"], 512)
        self.assertEqual(self.data["expanded"]["sram_bytes"], 128 * 1024)
        self.assertEqual(self.data["expanded"]["sram_banks"], 16)

    def test_generation10_id_widths(self):
        for name, width in self.data["id_width_bits"].items():
            self.assertGreaterEqual(width, 16, name)

    def test_full_mbc5_bank_reference(self):
        far = self.data["far_reference"]
        self.assertGreaterEqual(far["bank_bits"], 9)
        self.assertEqual(far["address_bits"], 16)
        self.assertGreaterEqual(far["storage_bytes"], 4)


if __name__ == "__main__":
    unittest.main()
