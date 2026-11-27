"""Checkout relocation must not rename the installed Android contract."""
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "pgs"

class PgsProjectLayoutTests(unittest.TestCase):
    def test_tracked_directory_is_pgs(self):
        tracked = subprocess.check_output(
            ["git", "ls-files", "-z"], cwd=ROOT
        ).decode("utf-8").split("\0")
        self.assertTrue(any(p.startswith("pgs/") for p in tracked))
        self.assertFalse(any(p.startswith("pgrazor/") for p in tracked))
        for name in ("build.py", "native/CMakeLists.txt", "VERSION",
                     "PGS_LAST_VERSION_CODE", "pgs_update.py"):
            self.assertTrue((PROJECT / name).is_file(), name)

    def test_new_runtime_paths_and_installed_identity(self):
        bootstrap = (PROJECT / "src/dev/pgs/BootstrapProvider.java").read_text(encoding="utf-8")
        packer = (PROJECT / "nonroot.py").read_text(encoding="utf-8")
        updater = (PROJECT / "pgs_update.py").read_text(encoding="utf-8")
        self.assertIn('copyAsset(context,"pgs/embedded-agent.js"', bootstrap)
        self.assertNotIn('copyAsset(context,"pgrazor/embedded-agent.js"', bootstrap)
        self.assertIn("assets/pgs/embedded-agent.js", packer)
        self.assertIn('GAME_PACKAGE = "com.nianticlabs.pokemongo"', updater)
        self.assertIn("d95c6bdfcbd91dc5c9cde698487c88e4994771a475e4efde4567b8d5f44e96cf", updater)

    def test_ci_and_manual_release_paths(self):
        flow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertIn("-s pgs/test", flow)
        self.assertIn("pgs/build.py", flow)
        self.assertIn("pgs/rooted_installer.py", flow)
        self.assertNotIn("pgrazor/", flow)
        release = (ROOT / ".github/workflows/pgs-v0.0.2-release.yml").read_text(encoding="utf-8")
        self.assertIn("  workflow_dispatch:", release)
        self.assertNotIn("\n  push:", release)

    def test_legacy_local_inputs_and_vendor_attributes(self):
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
        for path in ("/pgrazor/", "/pgs/build-retention.json", "/pgs/branding/discord/",
                     "**/input/", "**/build/"):
            self.assertIn(path, ignore)
        self.assertIn("pgs/vendor/frida-java-bridge*.js -text", attributes)
        self.assertIn("pgs/vendor/COPYING.frida-tools -text", attributes)

if __name__ == "__main__":
    unittest.main()
