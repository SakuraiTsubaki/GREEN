from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class GreenExpansionTests(unittest.TestCase):
    def test_capacity_contract(self):
        data = json.loads((ROOT / "config/capacity.json").read_text(encoding="utf-8"))
        self.assertEqual(data["target"], "GREEN")
        self.assertGreaterEqual(data["policy_target_generation"], 10)
        for name in ("species", "forms", "moves", "abilities", "items", "types"):
            self.assertGreaterEqual(data["canonical_ids"][name]["bits"], 16)
        for name in ("maps", "scripts", "text", "graphics", "audio"):
            self.assertGreaterEqual(data["resource_keys"][name]["bits"], 32)

    def test_engine_pin_and_profile(self):
        data = json.loads((ROOT / "config/capacity.json").read_text(encoding="utf-8"))
        self.assertEqual(data["engine"]["build_profile"], "leafgreen")
        self.assertEqual(
            data["engine"]["verified_ref"],
            "75b806a3ab57a81ff1eb6179288981f0b3cc3050",
        )

    def test_engine_patch_bundle(self):
        patch_dir = ROOT / "patches/pokeemerald-expansion"
        names = sorted(p.name for p in patch_dir.glob("*.patch"))
        self.assertEqual(names, [
            "0001-green-expand-persistent-species-item-ids.patch",
            "0002-green-runtime-identity.patch",
        ])
        first = (patch_dir / names[0]).read_text(encoding="utf-8")
        self.assertIn("u16 species", first)
        self.assertIn("u16 heldItem", first)
        self.assertIn("MOVES_COUNT_ALL <= (1 << 11)", first)

    def test_source_save_boundary(self):
        data = json.loads((ROOT / "config/capacity.json").read_text(encoding="utf-8"))
        source = data["source_evidence"]["japanese"]
        self.assertEqual(source["main_data_start"], 0x2598)
        self.assertEqual(source["checksum_offset"], 0x3594)
        self.assertTrue(source["checksum_verified_on_supplied_saves"])


if __name__ == "__main__":
    unittest.main()
