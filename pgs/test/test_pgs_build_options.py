"""Regression tests for PGS-first build settings without SDK or signing keys."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build


class PgsBuildOptionTests(unittest.TestCase):
    def test_canonical_options_ignore_retired_names(self):
        self.assertEqual(build.build_setting("PGS_BUILD_TOOLS", "36.1.0", environ={}), "36.1.0")
        self.assertEqual(build.build_setting("PGS_BUILD_TOOLS", "36.1.0",
                                            environ={"PGRAZOR_BUILD_TOOLS": "36.0.0"}), "36.1.0")
        self.assertEqual(build.build_setting("PGS_ANDROID_PLATFORM", "android-36.1",
                                            environ={"PGRAZOR_ANDROID_PLATFORM": "android-36"}), "android-36.1")

    def test_pgs_wins_without_modifying_environment(self):
        env = {"PGS_BUILD_TOOLS": "36.1.0", "PGRAZOR_BUILD_TOOLS": "36.0.0"}
        before = dict(env)
        self.assertEqual(build.build_setting("PGS_BUILD_TOOLS", "36.0.0", environ=env), "36.1.0")
        self.assertEqual(env, before)

    def test_empty_primary_uses_default(self):
        self.assertEqual(build.build_setting("PGS_BUILD_TOOLS", "36.1.0",
                                            environ={"PGS_BUILD_TOOLS": "",
                                                     "PGRAZOR_BUILD_TOOLS": "36.0.0"}), "36.1.0")

    def test_build_version_uses_only_pgs_or_ledger(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "VERSION").write_text("v0.0.2", encoding="utf-8")
            with patch.dict(build.os.environ, {"PGRAZOR_VERSION": "v0.1.2"}, clear=True):
                self.assertEqual(build.release_version(root), "v0.0.2")
            with patch.dict(build.os.environ,
                            {"PGS_VERSION": "v0.0.3", "PGRAZOR_VERSION": "v0.1.2"},
                            clear=True):
                self.assertEqual(build.release_version(root), "v0.0.3")
            with patch.dict(build.os.environ, {"PGS_VERSION": "bad version"}, clear=True):
                with self.assertRaisesRegex(ValueError, "Invalid PGS version"):
                    build.release_version(root)

    def test_signing_setting_pgs_priority_and_legacy_fallback(self):
        self.assertEqual(build.signing_setting("KEYSTORE", environ={"PGS_KEYSTORE": "new", "PGRAZOR_KEYSTORE": "old"}), "new")
        self.assertEqual(build.signing_setting("KEYSTORE", environ={"PGRAZOR_KEYSTORE": "old"}), "old")
        self.assertIsNone(build.signing_setting("KEYSTORE", environ={}))
        with tempfile.TemporaryDirectory() as folder:
            key = Path(folder) / "existing.jks"
            key.write_bytes(b"fixture")
            env = {"PGS_KEYSTORE": str(key), "PGS_KEY_ALIAS": "alias",
                   "PGS_STORE_PASSWORD": "fixture-store", "PGS_KEY_PASSWORD": "fixture-key"}
            with patch.dict(build.os.environ, env, clear=True), patch.object(build, "run") as run:
                args = build.signing_args()
                self.assertEqual(args[1], key)
                self.assertEqual(args[-1], "alias")
                self.assertIn("env:PGS_STORE_PASSWORD", args)
                run.assert_not_called()
            with patch.dict(build.os.environ, {"PGS_KEYSTORE": ""}, clear=True):
                with self.assertRaises(RuntimeError):
                    build.signing_args()

    def test_workflows_use_pgs_nonsecret_build_options(self):
        workflows = Path(__file__).resolve().parents[2] / '.github' / 'workflows'
        for name in ('ci.yml', 'pgs-build.yml'):
            with self.subTest(workflow=name):
                source = (workflows / name).read_text(encoding='utf-8')
                for option in ('BUILD_TOOLS', 'ANDROID_PLATFORM', 'VERSION'):
                    self.assertNotIn('PGRAZOR_' + option + ':', source)
                self.assertIn('PGS_BUILD_TOOLS:', source)
                self.assertIn('PGS_ANDROID_PLATFORM:', source)
                if name == 'pgs-build.yml':
                    self.assertIn('PGS_VERSION:', source)

    def test_historical_publication_workflows_are_inert(self):
        workflows = Path(__file__).resolve().parents[2] / '.github/workflows'
        for name in ('release.yml', 'pgs-v0.0.1-release.yml', 'pgs-v0.0.2-release.yml',
                     'pgs-same-package-update.yml'):
            with self.subTest(workflow=name):
                flow = (workflows / name).read_text(encoding='utf-8')
                self.assertIn('  workflow_dispatch:', flow)
                self.assertIn('contents: read', flow)
                self.assertIn('exit 1', flow)
                for forbidden in ('secrets.', 'contents: write', 'actions/checkout', 'gh release',
                                  'tools/private_input.py', 'upload-artifact', '\n  push:', '\n  pull_request:'):
                    self.assertNotIn(forbidden, flow)


if __name__ == "__main__":
    unittest.main()
