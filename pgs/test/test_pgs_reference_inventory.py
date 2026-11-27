"""Offline identity inventory checks; no game input or secrets."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from pgs_reference_inventory import scan, text_count


class PgsReferenceInventoryTests(unittest.TestCase):
    def test_counts_case_variants_and_excludes_binary(self):
        self.assertEqual(text_count(b"PGRAZOR pgrazor PgRazor"), 3)
        self.assertEqual(text_count(b"PGS"), 0)
        self.assertIsNone(text_count(b"\x00pgrazor"))
        self.assertIsNone(text_count(b"\xff"))

    @unittest.skipUnless((ROOT / ".git").exists(), "Requires a Git checkout")
    def test_full_tracked_tree(self):
        result = scan(ROOT)
        self.assertGreater(result["tracked_files"], 0)
        self.assertLessEqual(result["text_files"], result["tracked_files"])
        self.assertEqual(result["tracked_name_matches"], [])
        self.assertEqual(result["remaining_files"], len(result["files"]))
        self.assertEqual(result["remaining_occurrences"],
                         sum(row["occurrences"] for row in result["files"]))
        self.assertEqual(result["remaining_occurrences"],
                         sum(result["remaining_by_category"].values()))
        self.assertTrue(all(row["path"] != "docs/PGS_REMAINING_REFERENCES.json"
                            for row in result["files"]))
        summary = {key: val for key, val in result.items() if key != "files"}
        print("PGS fresh tracked-reference inventory: " + json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
