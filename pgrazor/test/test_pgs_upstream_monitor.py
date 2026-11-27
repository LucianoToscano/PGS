import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import pgs_upstream_monitor as monitor


class UpstreamMonitorTests(unittest.TestCase):
    def test_unchanged(self):
        result = monitor.receipt(monitor.BASELINE)
        self.assertEqual(result["status"], "unchanged")
        self.assertFalse(result["merge_performed"])

    def test_changed_requires_review(self):
        result = monitor.receipt("a" * 40)
        self.assertEqual(result["status"], "review_required")
        self.assertFalse(result["source_modified"])

    def test_parse_exact_ref(self):
        self.assertEqual(monitor.parse_remote(monitor.BASELINE + "\trefs/heads/main\n"), monitor.BASELINE)
        for invalid in ("", "bad refs/heads/main", monitor.BASELINE + " refs/heads/other",
                        monitor.BASELINE + " refs/heads/main\nextra"):
            with self.assertRaises(ValueError):
                monitor.parse_remote(invalid)


if __name__ == "__main__":
    unittest.main()
