import unittest

from tools.patch_species_runtime import (
    PAGE_DIRECTORY_BYTES,
    PAGE_DIRECTORY_CPU,
    READ4_FROM_BANK9_LOW,
    READ4_HELPER,
    READ4_HELPER_END,
    RUNTIME_CPU,
    RUNTIME_END,
    runtime_code,
)


class SpeciesRuntimeTests(unittest.TestCase):
    def test_fixed_read4_layout(self):
        self.assertEqual(READ4_HELPER, 0x009B)
        self.assertEqual(READ4_HELPER_END, 0x00BD)
        self.assertEqual(len(READ4_FROM_BANK9_LOW), 34)
        self.assertIn(b"\xEA\x00\x30", READ4_FROM_BANK9_LOW)

    def test_runtime_layout(self):
        self.assertEqual(RUNTIME_CPU, 0x4000)
        self.assertEqual(RUNTIME_END, 0x407D)
        self.assertEqual(PAGE_DIRECTORY_CPU, 0x4100)
        self.assertEqual(PAGE_DIRECTORY_BYTES, 1024)

    def test_revision_specific_loader_call(self):
        rev0 = runtime_code(0x2F2E)
        reva = runtime_code(0x2F1C)
        self.assertEqual(len(rev0), 125)
        self.assertEqual(len(reva), 125)
        self.assertIn(b"\xCD\x2E\x2F", rev0)
        self.assertIn(b"\xCD\x1C\x2F", reva)

    def test_resolver_calls_fixed_data_reader(self):
        code = runtime_code(0x2F2E)
        self.assertIn(b"\xCD\x9B\x00", code)
        self.assertIn(b"\x01\x00\x41", code)


if __name__ == "__main__":
    unittest.main()
