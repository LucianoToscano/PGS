import sys
import unittest
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
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

    def test_origin_is_derived_from_notice(self):
        self.assertTrue(monitor.UPSTREAM.startswith("https://github.com/"))
        self.assertEqual(monitor.read_origin(monitor.ROOT / "NOTICE"), (monitor.UPSTREAM, monitor.BASELINE))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "NOTICE"
            path.write_text("Original source: file:///tmp/local\nUpstream baseline: " + monitor.BASELINE, encoding="utf-8")
            with self.assertRaises(ValueError):
                monitor.read_origin(path)

    def test_parse_exact_ref(self):
        self.assertEqual(monitor.parse_remote(monitor.BASELINE + "\trefs/heads/main\n"), monitor.BASELINE)
        for invalid in ("", "bad refs/heads/main", monitor.BASELINE + " refs/heads/other",
                        monitor.BASELINE + " refs/heads/main\nextra"):
            with self.assertRaises(ValueError):
                monitor.parse_remote(invalid)


if __name__ == "__main__":
    unittest.main()
