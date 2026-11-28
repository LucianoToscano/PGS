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

    def test_comparison_reports_metadata_without_claiming_conflicts(self):
        base, head = monitor.BASELINE, "a" * 40
        upstream_name = monitor.urlsplit(monitor.UPSTREAM).path.rsplit("/", 1)[1].removesuffix(".git")
        name = upstream_name.lower() + "/VERSION"
        data = {"base_commit": {"sha": base}, "status": "ahead", "ahead_by": 2,
                "behind_by": 0, "total_commits": 2,
                "commits": [{"sha": head, "commit": {"message": "Fix sample\\nbody"}}],
                "files": [{"filename": name, "status": "modified", "additions": 1, "deletions": 1}]}
        result = monitor.comparison_summary(data, base, head)
        self.assertEqual(result["commits"][0]["category_hint"], "fix")
        self.assertEqual(result["files"][0]["local_path"], "pgs/VERSION")
        self.assertTrue(result["commit_list_may_be_truncated"])
        self.assertFalse(result["conflicts_confirmed"])
        self.assertIn(base + "..." + head, monitor.compare_url(base, head))
        data["base_commit"]["sha"] = "b" * 40
        with self.assertRaises(ValueError):
            monitor.comparison_summary(data, base, head)

    def test_unchanged_has_no_network_comparison(self):
        self.assertEqual(monitor.compare_metadata(monitor.BASELINE, monitor.BASELINE)["files"], [])

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
