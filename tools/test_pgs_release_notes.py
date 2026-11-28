from pathlib import Path
import tempfile
import unittest
from pgs_release_notes import render

class ReleaseNotesTests(unittest.TestCase):
    def test_current_notes(self):
        notes = render("v0.0.5")
        self.assertIn("Português (Brasil)", notes)
        self.assertIn("2026111608", notes)
        self.assertEqual(notes.count("# PGS v0.0.5"), 2)

    def test_invalid_version_and_missing_translation(self):
        with self.assertRaises(ValueError):
            render("../bad")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs/releases").mkdir(parents=True)
            (root / "docs/releases/v1.2.3.md").write_text("# PGS v1.2.3\n", encoding="utf-8")
            with self.assertRaises(FileNotFoundError):
                render("v1.2.3", root)

if __name__ == "__main__":
    unittest.main()
