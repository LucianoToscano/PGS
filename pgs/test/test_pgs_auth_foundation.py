"""Device-free tests for the independent, disabled PGS Auth foundation."""
from pathlib import Path
import subprocess
import tempfile
import unittest

from test_control_java import java_tools

ROOT = Path(__file__).resolve().parents[1]


class PgsAuthFoundationTests(unittest.TestCase):
    def test_java_lifecycle_and_diagnostics(self):
        javac, java = java_tools()
        source = ROOT / "src/dev/pgs"
        with tempfile.TemporaryDirectory(prefix="pgs-auth-") as work:
            subprocess.run(
                [str(javac), "-encoding", "UTF-8", "-source", "8", "-target", "8",
                 "-d", work, str(source / "PgsAuthConfig.java"),
                 str(source / "PgsAuthManager.java"), str(source / "PgsAuthAttempt.java"),
                 str(ROOT / "test/PgsAuthFoundationTest.java")],
                check=True, capture_output=True, timeout=45)
            result = subprocess.run(
                [str(java), "-cp", work, "dev.pgs.PgsAuthFoundationTest"],
                check=True, capture_output=True, text=True, timeout=20)
            self.assertIn("PASS (no live authentication)", result.stdout)

    def test_no_new_network_or_game_integration(self):
        source = ROOT / "src/dev/pgs"
        for name in ("PgsAuthConfig", "PgsAuthManager", "PgsAuthAttempt"):
            text = (source / (name + ".java")).read_text(encoding="utf-8")
            for forbidden in ("android.", "java.net.", "https://", "http://",
                              "googleusercontent", "client_id", "access_token",
                              "refresh_token", "id_token", "GameBridgeDispatch"):
                self.assertNotIn(forbidden, text, name)
        manifest = (ROOT / "AndroidManifest.xml").read_text(encoding="utf-8")
        self.assertNotIn("PgsAuthActivity", manifest)
        bootstrap = (source / "BootstrapProvider.java").read_text(encoding="utf-8")
        self.assertIn("configureBrowserSignIn(false)", bootstrap)
        self.assertNotIn("PgsAuthManager", bootstrap)


if __name__ == "__main__":
    unittest.main()
