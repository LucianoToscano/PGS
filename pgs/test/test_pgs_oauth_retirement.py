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
    def test_legacy_options_fail_before_input_or_build(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "missing.apk"
            output = Path(folder) / "must-not-exist.apk"
            with self.assertRaisesRegex(ValueError, "OAuth is retired"):
                nonroot.rewrite_apk(source, output, google_browser_login=True)
            self.assertFalse(output.exists())
            with self.assertRaisesRegex(ValueError, "OAuth is retired"):
                nonroot.package(source, google_browser_login=True)
            with patch.object(nonroot, "command") as command:
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit):
                        nonroot.main(["--apk", str(source), "--google-browser-login"])
                command.assert_not_called()

    def test_legacy_mode_cannot_reactivate_browser(self):
        bootstrap = (PROJECT / "src/dev/pgs/BootstrapProvider.java").read_text(encoding="utf-8")
        self.assertIn("configureBrowserSignIn(false)", bootstrap)
        self.assertIn('.put("googleBrowserLogin",false)', bootstrap)
        self.assertNotIn('optBoolean("googleBrowserLogin"', bootstrap)
        for file in ("axml.py", "src/dev/pgs/GoogleBrowserAuth.java", "src/dev/pgs/GoogleAuthActivity.java"):
            content = (PROJECT / file).read_text(encoding="utf-8")
            self.assertNotIn("googleusercontent" + ".apps", content)
            self.assertNotIn(".apps.googleusercontent" + ".com", content)
            self.assertNotIn("oauth2.googleapis" + ".com/token", content)

    def test_actual_retired_java_api_is_inert(self):
        from test_control_java import java_tools
        javac, java = java_tools()
        with tempfile.TemporaryDirectory() as folder:
            work = Path(folder)
            sources = {
                "android/app/Activity.java": "package android.app; public class Activity {}",
                "android/net/Uri.java": "package android.net; public class Uri {}",
                "RetiredAuthTest.java": """
import dev.pgs.GoogleBrowserAuth;
import android.app.Activity;
import android.net.Uri;
public class RetiredAuthTest {
    public static void main(String[] args) {
        if (GoogleBrowserAuth.begin(new Activity()) != null) throw new AssertionError("begin");
        if (GoogleBrowserAuth.handleRedirect(new Uri())) throw new AssertionError("redirect");
        if (GoogleBrowserAuth.takeResult("synthetic") != null) throw new AssertionError("result");
        GoogleBrowserAuth.cancel("synthetic");
        GoogleBrowserAuth.onHostPaused(new Activity());
        GoogleBrowserAuth.onHostResumed(new Activity());
        if (GoogleBrowserAuth.takeResult(null) != null) throw new AssertionError("null result");
    }
}
""",
            }
            paths = []
            for relative, text in sources.items():
                path = work / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
                paths.append(str(path))
            paths.append(str(PROJECT / "src/dev/pgs/GoogleBrowserAuth.java"))
            subprocess.run([str(javac), "-encoding", "UTF-8", "-d", str(work), *paths],
                           check=True, capture_output=True, timeout=30)
            subprocess.run([str(java), "-cp", str(work), "RetiredAuthTest"],
                           check=True, capture_output=True, timeout=15)

    def test_request_scoped_candidate_workflow_only_uploads_receipts(self):
        flow = (ROOT / ".github/workflows/pgs-build.yml").read_text(encoding="utf-8")
        self.assertIn("  workflow_dispatch:", flow)
        self.assertIn("  push:\n    branches: [main]\n    paths: [build-request.json]", flow)
        self.assertNotIn("\n  pull_request:", flow)
        self.assertIn("default: false", flow)
        self.assertIn("python -B tools/pgs_build_request.py --gate", flow)
        self.assertIn("    needs: request", flow)
        self.assertIn("needs.request.outputs.enabled == 'true'", flow)
        self.assertIn("github.ref == 'refs/heads/main'", flow)
        self.assertIn("contents: read", flow)
        self.assertEqual(flow.count("contents: write"), 1)
        self.assertIn("    permissions:\n      contents: write", flow)
        self.assertIn("persist-credentials: false", flow)
        self.assertNotIn("PGS_INPUT_URL", flow)
        self.assertNotIn("PGS_INPUT_TOKEN", flow)
        self.assertNotIn("gh release upload", flow)
        self.assertNotIn("gh release edit", flow)
        self.assertNotIn("gh release create", flow)
        self.assertNotIn("--google-browser-login", flow)
        self.assertIn("test -f \"$PGS_KEYSTORE\"", flow)
        early = flow.split("name: Check required private configuration before installing tools", 1)[1].split("      - uses:", 1)[0]
        self.assertLess(flow.index("name: Check required private configuration"), flow.index("name: Install pinned toolchain"))
        for name in ("PGS_KEYSTORE_BASE64", "PGS_KEY_ALIAS", "PGS_STORE_PASSWORD", "PGS_KEY_PASSWORD"):
            self.assertIn(name + ":", early)
        self.assertIn('[[ -z "${!name}" ]]', early)
        self.assertIn('echo "::error::Missing required configuration: $name.', early)
        self.assertIn('test "$missing" = 0', early)
        self.assertNotIn("set -x", early)
        self.assertNotIn("private_input.py", early)
        self.assertLess(flow.index("name: Check authorized draft input"), flow.index("name: Install pinned toolchain"))
        self.assertIn("tools/pgs_pinned_input.py --preflight", flow)
        retrieval = flow.split("name: Retrieve and verify authorized original", 1)[1].split("      - name:", 1)[0]
        self.assertIn("GH_TOKEN:", retrieval)
        self.assertNotIn("KEYSTORE", retrieval)
        key_load = flow.split("name: Load existing signer only after input verification", 1)[1].split("      - name:", 1)[0]
        self.assertIn("tools/pgs_pinned_input.py --load-key", key_load)
        self.assertNotIn("GH_TOKEN:", key_load)
        self.assertIn("d['version_code']==int(os.environ['PGS_EXPECTED_VERSION_CODE'])", flow)
        self.assertIn("d['pgs_version']==os.environ['PGS_VERSION']", flow)
        self.assertIn("Check previous signed candidate and unused draft target", flow)
        upload = flow.split("name: Upload verification receipts only", 1)[1].split("      - name:", 1)[0]
        self.assertIn("/PGS.json", upload)
        self.assertIn("/build-info.json", upload)
        self.assertNotIn(".apk", upload)
        self.assertNotIn(".jks", upload)
        self.assertIn("if: always()", flow)
        self.assertIn("retain_authorized_candidate:", flow)
        retention_input = flow.split("      retain_authorized_candidate:", 1)[1].split("permissions:", 1)[0]
        self.assertIn("default: false", retention_input)
        self.assertIn("PGS_MANUAL_AUTHORIZED: ${{ inputs.authorized_input }}", flow)
        self.assertIn("PGS_RETAIN_AUTHORIZED: ${{ needs.request.outputs.retain }}", flow)
        self.assertIn("if: needs.request.outputs.retain == 'true'", flow)
        retained = flow.split("name: Retain authorized signed candidate", 1)[1].split("      - name:", 1)[0]
        self.assertIn('rm -f -- "$PGS_KEYSTORE"', retained)
        self.assertIn("python -B tools/pgs_candidate_draft.py", retained)
        self.assertNotIn("KEYSTORE_BASE64", retained)
        self.assertLess(flow.index("name: Build and verify complete candidate"), flow.index("name: Retain authorized signed candidate"))
        self.assertEqual(flow.count("actions/upload-artifact@"), 1)


if __name__ == "__main__":
    unittest.main()
