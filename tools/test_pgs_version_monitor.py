"""Offline regression tests for the PGS public-version monitor."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pgs_version_monitor import latest_version, new_version, reviewed_version, version_key


class PgsVersionMonitorTests(unittest.TestCase):
    def test_latest_stable_heading_and_numeric_sort(self):
        catalog = ('<h5><a>Pokémon GO 0.439.12</a></h5>'
                   '<h5><a>Pokémon GO 0.440.0</a></h5>'
                   '<h5>Pokémon GO 0.999.0 beta</h5>'
                   '<h5>Another game 99.0.0</h5>')
        self.assertEqual(latest_version(catalog), '0.440.0')

    def test_fail_closed_on_missing_versions(self):
        with self.assertRaises(ValueError):
            latest_version('<html><h5>Blocked</h5></html>')
        for invalid in ('0.440', 'v0.440.0', '0.440.0-beta', ''):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                version_key(invalid)

    def test_only_newer_version_creates_alert(self):
        self.assertEqual(new_version('0.440.0', '0.439.0'), '0.440.0')
        self.assertEqual(new_version('0.439.0', '0.439.0'), '')
        self.assertEqual(new_version('0.438.0', '0.439.0'), '')
        self.assertEqual(new_version('0.440.0', ''), '')

    def test_reviewed_profile_fallback_never_decreases(self):
        self.assertEqual(reviewed_version('0.439.0'), '0.439.0')
        self.assertEqual(reviewed_version('0.439.0', '0.438.0'), '0.439.0')
        self.assertEqual(reviewed_version('0.439.0', '0.440.0'), '0.440.0')
        with self.assertRaises(ValueError):
            reviewed_version('0.439.0', '0.440.0 beta')


if __name__ == '__main__':
    unittest.main()
