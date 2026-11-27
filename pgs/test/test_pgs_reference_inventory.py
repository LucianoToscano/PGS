"""Offline identity inventory checks; no game input or secrets."""
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from pgs_reference_inventory import abbreviation_counts, scan, snapshot_differences, text_count


class PgsReferenceInventoryTests(unittest.TestCase):
    def test_counts_case_variants_and_excludes_binary(self):
        self.assertEqual(text_count(b"PGRAZOR pgrazor PgRazor"), 3)
        self.assertEqual(text_count(b"PGS"), 0)
        self.assertIsNone(text_count(b"\x00pgrazor"))
        self.assertIsNone(text_count(b"\xff"))

    def test_abbreviations_are_counted_separately(self):
        data = b"PGR_ACCOUNTS_H_ PGR_ACC_CMD_NONE pgr_battle_api_v1 PgrSpinHostConfig PGS_ACCOUNTS_H_ XPGR_TEST"
        self.assertEqual(abbreviation_counts(data), {"uppercase": 2, "lowercase": 1, "camelcase": 1})
        self.assertEqual(abbreviation_counts(b"PGS_TEST pgs_test PgsType"), {})
        self.assertIsNone(abbreviation_counts(b"\x00PGR_TEST"))
        self.assertIsNone(abbreviation_counts(b"\xff"))

    def test_snapshot_differences_reports_exact_paths_and_counts(self):
        previous = {"files": [{"path": "a", "occurrences": 9}, {"path": "b", "occurrences": 1}]}
        current = {"files": [{"path": "b", "occurrences": 1}, {"path": "c", "occurrences": 2}]}
        self.assertEqual(snapshot_differences(previous, current), [
            {"path": "a", "snapshot": 9, "actual": 0},
            {"path": "c", "snapshot": 0, "actual": 2},
        ])
        self.assertEqual(snapshot_differences(current, current), [])

    def test_index_is_independent_of_worktree_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            (root / "docs").mkdir()
            (root / "docs/PGS_REMAINING_REFERENCES.json").write_text('{"files": []}', encoding="utf-8")
            (root / "notes.txt").write_bytes(b"PGRAZOR pgrazor PGR_TEST PgrTest pgr_test\n")
            (root / "binary.bin").write_bytes(b"\x00pgrazor")
            subprocess.run(["git", "add", "--all"], cwd=root, check=True)
            (root / "notes.txt").write_bytes(b"PGS\n")
            (root / "untracked.txt").write_bytes(b"pgrazor")
            indexed = scan(root)
            checkout = scan(root, worktree=True)
            self.assertEqual(indexed["tracked_files"], 2)
            self.assertEqual(indexed["text_files"], 1)
            self.assertEqual(indexed["remaining_occurrences"], 2)
            self.assertEqual(checkout["remaining_occurrences"], 0)
            self.assertEqual(indexed["abbreviations"]["remaining_occurrences"], 3)
            self.assertEqual(checkout["abbreviations"]["remaining_occurrences"], 0)
            self.assertEqual(snapshot_differences(indexed, checkout), [
                {"path": "notes.txt", "snapshot": 2, "actual": 0},
            ])

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
        abbreviations = result["abbreviations"]
        self.assertEqual(abbreviations["remaining_files"], len(abbreviations["files"]))
        self.assertEqual(abbreviations["remaining_occurrences"], sum(row["occurrences"] for row in abbreviations["files"]))
        self.assertEqual(abbreviations["remaining_occurrences"], sum(abbreviations["by_form"].values()))
        summary = {key: val for key, val in result.items() if key not in ("files", "abbreviations")}
        print("PGS abbreviated reference summary: " + json.dumps({k: v for k, v in abbreviations.items() if k != "files"}, sort_keys=True))
        print("PGS abbreviated reference files: " + json.dumps(abbreviations["files"], sort_keys=True))
        print("PGS fresh tracked-reference inventory: " + json.dumps(summary, sort_keys=True))
        previous = json.loads((ROOT / "docs/PGS_REMAINING_REFERENCES.json").read_text(encoding="utf-8"))
        differences = snapshot_differences(previous, result)
        print("PGS snapshot differences: " + json.dumps(differences, sort_keys=True))
        checkout = scan(ROOT, worktree=True)
        print("PGS index/worktree differences: " + json.dumps(snapshot_differences(result, checkout), sort_keys=True))
        self.assertEqual(differences, [], "The inventory must match indexed Git text")
        self.assertEqual(result["remaining_occurrences"], previous["remaining_occurrences"])
        self.assertEqual(result["remaining_by_category"], previous["remaining_by_category"])


if __name__ == "__main__":
    unittest.main()
