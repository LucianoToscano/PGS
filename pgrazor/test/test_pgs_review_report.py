import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import pgs_review_report as review


class PGSReviewTests(unittest.TestCase):
    def test_report_counts_and_review_categories(self):
        result = review.report(["LICENSE", "pgrazor/native/example.cpp",
                                ".github/workflows/ci.yml", "docs/BUILDING.md",
                                "docs/BUILDING.md", "pgrazor/test/test_example.py",
                                "website/src/App.jsx"])
        self.assertEqual(result["changed_paths"], 6)
        self.assertEqual(result["specialist_review_categories"],
                         ["automation", "license", "native"])
        self.assertFalse(result["automatic_merge"])
        self.assertFalse(result["automatic_code_changes"])

    def test_categories(self):
        self.assertEqual(review.category("pgrazor/root-installer/AndroidManifest.xml"), "android")
        self.assertEqual(review.category("pgrazor/build.py"), "build_or_runtime")
        self.assertEqual(review.category("unknown.bin"), "other")
        self.assertEqual(review.report([])["changed_paths"], 0)

    def test_revision_validation(self):
        self.assertEqual(review.revision("a" * 40), "a" * 40)
        for value in ("HEAD", "--help", "f" * 39, "z" * 40):
            with self.assertRaises(ValueError):
                review.revision(value)


if __name__ == "__main__":
    unittest.main()
