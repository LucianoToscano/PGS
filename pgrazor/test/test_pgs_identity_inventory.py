import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import pgs_identity_inventory as scan


class IdentityInventoryTest(unittest.TestCase):
    def test_classifies_history_without_reading_vendor_or_untracked(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            files = {
                "pgrazor/src/Example.java": "package dev.pgrazor; // PGRazor",
                "tools/build.py": "PGRAZOR_KEY_ALIAS = 'secret-marker'",
                "docs/releases/v0.1.0.md": "PGRazor",
                "pgrazor/vendor/library.c": "pgrazor_native_api",
                "untracked.txt": "PGRazor",
            }
            for name, value in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(value, encoding="utf-8")
            result = scan.inventory(root, [Path(name) for name in files if name != "untracked.txt"])
            self.assertEqual(result["totals"]["active"]["java_namespace"], 1)
            self.assertEqual(result["totals"]["active"]["legacy_env"], 1)
            self.assertEqual(result["totals"]["history"]["legacy_brand"], 1)
            self.assertEqual(len(result["files"]), 3)
            self.assertNotIn("secret-marker", str(result))
            self.assertNotIn("untracked.txt", str(result))

    def test_rejects_parent_traversal(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                scan.inventory(Path(folder), [Path("../outside.txt")])


if __name__ == "__main__":
    unittest.main()
