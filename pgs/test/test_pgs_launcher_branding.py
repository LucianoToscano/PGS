"""Verify the official launcher art and all three packaging paths."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
import build


class PgsLauncherBrandingTests(unittest.TestCase):
    def test_official_png_identity(self):
        path = build.launcher_branding_asset()
        self.assertEqual(path, PROJECT / "branding/pgs-shield.png")
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), build.LAUNCHER_BRANDING_SHA256)
        self.assertTrue(path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))

    def test_modified_art_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "branding").mkdir()
            (root / "branding/pgs-shield.png").write_bytes(b"modified")
            with patch.object(build, "ROOT", root):
                with self.assertRaisesRegex(RuntimeError, "verified original"):
                    build.launcher_branding_asset()

    def test_launcher_uses_official_asset_and_preserves_accessibility(self):
        source = (PROJECT / "src/dev/pgs/Pad.java").read_text(encoding="utf-8")
        self.assertIn('PgAssets.open(context, "' + build.LAUNCHER_BRANDING_ASSET + '")', source)
        self.assertIn("new PgsIcon(host)", source)
        self.assertNotIn("RazorIcon", source)
        self.assertIn("draggable(launcher,launcher,true)", source)
        self.assertIn("Control.desiredEnabled()", source)
        self.assertIn('canvas.drawText("PGS"', source)
        for name in ("build.py", "nonroot.py", "rooted.py"):
            text = (PROJECT / name).read_text(encoding="utf-8")
            self.assertIn("launcher_branding_asset()", text, name)


if __name__ == "__main__":
    unittest.main()
