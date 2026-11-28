"""Retired third-party OAuth and manual receipt-only candidate policy."""
from pathlib import Path
import io
import contextlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parent
sys.path.insert(0, str(PROJECT))
import axml
import nonroot


class PgsOauthRetirementTests(unittest.TestCase):
    def test_google_browser_login_accepted(self):
        # google_browser_login=True parameter is accepted without "OAuth is retired" rejection
        import inspect
        sig = inspect.signature(nonroot.rewrite_apk)
        self.assertIn("google_browser_login", sig.parameters)
        sig2 = inspect.signature(nonroot.package)
        self.assertIn("google_browser_login", sig2.parameters)
        # The ValueError for missing APK is expected; OAuth retirement error is gone
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "missing.apk"
            output = Path(folder) / "must-not-exist.apk"
            try:
                nonroot.rewrite_apk(source, output, google_browser_login=True)
            except ValueError as error:
                self.assertNotIn("OAuth is retired", str(error))
            except FileNotFoundError:
                pass  # missing APK is expected in this test
            self.assertFalse(output.exists())

    def test_google_browser_login_reads_mode(self):
        bootstrap = (PROJECT / "src/dev/pgs/BootstrapProvider.java").read_text(encoding="utf-8")
        # Reference v0.0.2 reads googleBrowserLogin from pgs/mode.json (opt-in, default false).
        self.assertIn('optBoolean("googleBrowserLogin"', bootstrap)
        self.assertIn("configureBrowserSignIn(", bootstrap)
        # GoogleBrowserAuth and GoogleAuthActivity exist as callback scaffolding.
        auth = (PROJECT / "src/dev/pgs/GoogleBrowserAuth.java").read_text(encoding="utf-8")
        self.assertIn("begin(", auth)
        self.assertIn("takeResult(", auth)
        self.assertIn("handleRedirect(", auth)
        activity = (PROJECT / "src/dev/pgs/GoogleAuthActivity.java").read_text(encoding="utf-8")
        self.assertIn("handleRedirect(", activity)
        self.assertIn("finish()", activity)

    def test_actual_browser_api_rejects_unsolicited_session_operations(self):
        # Compile the real API against the pinned Android SDK, not incomplete
        # stubs for the previously retired implementation. Do not launch a
        # browser or perform any network request.
        import build
        from test_control_java import java_tools
        javac, java = java_tools()
        if not build.ANDROID.is_file():
            self.skipTest("Android SDK required for the real browser API")
        with tempfile.TemporaryDirectory() as folder:
            work = Path(folder)
            control = work / "dev/pgs/Control.java"
            control.parent.mkdir(parents=True)
            control.write_text("package dev.pgs; public final class Control { public static void event(String a, String b) {} }", encoding="utf-8")
            driver = work / "NoPendingAuthTest.java"
            driver.write_text("""
import dev.pgs.GoogleBrowserAuth;
public final class NoPendingAuthTest {
    public static void main(String[] args) {
        if (GoogleBrowserAuth.handleRedirect(null)) throw new AssertionError("unsolicited redirect");
        if (GoogleBrowserAuth.takeResult("synthetic") != null) throw new AssertionError("unsolicited result");
        GoogleBrowserAuth.cancel("synthetic");
        GoogleBrowserAuth.onHostPaused(null);
        GoogleBrowserAuth.onHostResumed(null);
        if (GoogleBrowserAuth.takeResult(null) != null) throw new AssertionError("null result");
    }
}
""", encoding="utf-8")
            subprocess.run([str(javac), "-encoding", "UTF-8", "-cp", str(build.ANDROID), "-d", str(work),
                            str(control), str(driver), str(PROJECT / "src/dev/pgs/GoogleBrowserAuth.java")],
                           check=True, capture_output=True, timeout=30)
            import os
            subprocess.run([str(java), "-cp", str(work) + os.pathsep + str(build.ANDROID), "NoPendingAuthTest"],
                           check=True, capture_output=True, timeout=15)

    def test_manual_candidate_workflow_only_uploads_receipts(self):
        flow = (ROOT / ".github/workflows/pgs-v0.0.4-candidate.yml").read_text(encoding="utf-8")
        self.assertIn("  workflow_dispatch:", flow)
        self.assertNotIn("\n  push:", flow)
        self.assertNotIn("\n  pull_request:", flow)
        self.assertIn("default: false", flow)
        self.assertIn("inputs.authorized_input == true", flow)
        self.assertIn("github.ref == 'refs/heads/main'", flow)
        self.assertIn("contents: read", flow)
        self.assertNotIn("contents: write", flow)
        self.assertNotIn("gh release create", flow)
        self.assertIn("--google-browser-login", flow)
        self.assertIn("test -f \"$PGS_KEYSTORE\"", flow)
        early = flow.split("name: Check required private configuration before installing tools", 1)[1].split("      - uses:", 1)[0]
        self.assertLess(flow.index("name: Check required private configuration"), flow.index("name: Install pinned toolchain"))
        for name in ("PGS_INPUT_URL", "PGS_KEYSTORE_BASE64", "PGS_KEY_ALIAS", "PGS_STORE_PASSWORD", "PGS_KEY_PASSWORD"):
            self.assertIn(name + ":", early)
        self.assertIn('[[ -z "${!name}" ]]', early)
        self.assertIn('echo "::error::Missing required configuration: $name.', early)
        self.assertIn('test "$missing" = 0', early)
        self.assertNotIn("set -x", early)
        self.assertNotIn("private_input.py", early)
        self.assertIn("= 2026111606", flow)
        self.assertIn("d['version_code']==2026111607", flow)
        upload = flow.split("name: Upload verification receipts only", 1)[1].split("      - name:", 1)[0]
        self.assertIn("/PGS.json", upload)
        self.assertIn("/build-info.json", upload)
        self.assertNotIn(".apk", upload)
        self.assertNotIn(".jks", upload)
        self.assertIn("if: always()", flow)


if __name__ == "__main__":
    unittest.main()
