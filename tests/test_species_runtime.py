import unittest

from tools.patch_species_runtime import (
    RUNTIME_CPU,
    RUNTIME_FILE_OFFSET,
    RUNTIME_UNSUPPORTED,
    runtime_code,
)


class SpeciesRuntimeTests(unittest.TestCase):
    def test_runtime_location(self):
        self.assertEqual(RUNTIME_CPU, 0x4000)
        self.assertEqual(RUNTIME_FILE_OFFSET, 0x80000)
        self.assertEqual(RUNTIME_UNSUPPORTED, 0x4038)

    def test_revision_specific_loader_call(self):
        rev0 = runtime_code(0x2F2E)
        reva = runtime_code(0x2F1C)
        self.assertEqual(len(rev0), 0x3A)
        self.assertEqual(len(reva), 0x3A)
        self.assertEqual(rev0[:0x2B], reva[:0x2B])
        self.assertEqual(rev0[0x2B:0x2E], b"\xCD\x2E\x2F")
        self.assertEqual(reva[0x2B:0x2E], b"\xCD\x1C\x2F")
        self.assertEqual(rev0[0x2E:], reva[0x2E:])

    def test_runtime_uses_mbc5_farcall_bridge_for_mapping(self):
        code = runtime_code(0x2F2E)
        self.assertIn(b"\x21\x6F\x67\xCD\x68\x00", code)
        self.assertTrue(code.endswith(b"\x37\xC9"))


if __name__ == "__main__":
    unittest.main()
