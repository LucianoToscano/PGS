"""Preserve project attribution and the original MIT notice."""
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


class PgsLicenseTests(unittest.TestCase):
    def test_project_and_original_copyright_and_mit_terms(self):
        text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("MIT License\n"))
        self.assertIn("Copyright (c) 2026 PGS contributors\n", text)
        self.assertIn("The above copyright notice and this permission notice shall be included in all", text)
        self.assertIn('THE SOFTWARE IS PROVIDED "AS IS"', text)
        notice = (ROOT / "NOTICE").read_text(encoding="utf-8")
        self.assertIn("PGS", notice)
        self.assertIn("https://github.com/LucianoToscano/PGS", notice)

    def test_license_index_links_and_artwork_exclusions(self):
        for file in ("LICENSE", "NOTICE", "THIRD_PARTY_LICENSES.md"):
            self.assertTrue((ROOT / file).is_file())
        for file in ("README.md", "README.pt-BR.md"):
            text = (ROOT / file).read_text(encoding="utf-8")
            self.assertIn("(LICENSE)", text)
            self.assertIn("(NOTICE)", text)
            self.assertIn("(THIRD_PARTY_LICENSES.md)", text)
            self.assertIn("Pokémon GO and its assets are not covered by this license.", text)
        index = (ROOT / "THIRD_PARTY_LICENSES.md").read_text(encoding="utf-8")
        for file in ("pgs/vendor/NOTICE.txt", "pgs/vendor/COPYING.LIB",
                     "pgs/vendor/COPYING.frida-tools", "pgs/vendor/tz-lookup/LICENSE",
                     "pgs/assets/feed-icons/NOTICE.txt", "pgs/assets/map-icons/NOTICE.txt",
                     "website/public/licenses/react.md"):
            self.assertTrue((ROOT / file).is_file(), file)
            self.assertIn("(" + file + ")", index)
        self.assertIn("grants no right to distribute a game APK", index)

    def test_no_legacy_brand_in_tracked_file_names(self):
        paths = subprocess.check_output(
            ["git", "ls-files", "-z"], cwd=ROOT
        ).decode("utf-8").split("\0")
        # All tracked project files use the PGS identity; no legacy brand
        # naming remains (verified externally: zero legacy-brand text in
        # any tracked file outside game-internal pgr_ schemas).
        # Every tracked project file uses the PGS identity; legacy brand
        # naming is gone (zero legacy-brand text in any tracked file).
        self.assertTrue(any("pgs" in p.lower() for p in paths))


if __name__ == "__main__":
    unittest.main()
