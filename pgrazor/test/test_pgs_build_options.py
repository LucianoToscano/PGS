"""Regression tests for PGS-first build settings without SDK or signing keys."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import build


class PgsBuildOptionTests(unittest.TestCase):
    def test_default_and_legacy_fallback(self):
        self.assertEqual(build.build_setting("PGS_BUILD_TOOLS", "PGRAZOR_BUILD_TOOLS",
                                            "36.1.0", environ={}), "36.1.0")
        self.assertEqual(build.build_setting("PGS_BUILD_TOOLS", "PGRAZOR_BUILD_TOOLS",
                                            "36.1.0",
                                            environ={"PGRAZOR_BUILD_TOOLS": "36.0.0"}),
                         "36.0.0")
        self.assertEqual(build.build_setting("PGS_ANDROID_PLATFORM", "PGRAZOR_ANDROID_PLATFORM",
                                            "android-36.1",
                                            environ={"PGRAZOR_ANDROID_PLATFORM": "android-36"}),
                         "android-36")

    def test_pgs_wins_without_modifying_environment(self):
        env = {"PGS_BUILD_TOOLS": "36.1.0", "PGRAZOR_BUILD_TOOLS": "36.0.0"}
        before = dict(env)
        self.assertEqual(build.build_setting("PGS_BUILD_TOOLS", "PGRAZOR_BUILD_TOOLS",
                                            "36.1.0", environ=env), "36.1.0")
        self.assertEqual(env, before)

    def test_empty_primary_falls_back(self):
        self.assertEqual(build.build_setting("PGS_BUILD_TOOLS", "PGRAZOR_BUILD_TOOLS",
                                            "36.1.0",
                                            environ={"PGS_BUILD_TOOLS": "",
                                                     "PGRAZOR_BUILD_TOOLS": "36.0.0"}),
                         "36.0.0")

    def test_build_version_preserves_alias_and_pgs_priority(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "VERSION").write_text("v0.0.2", encoding="utf-8")
            with patch.dict(build.os.environ, {}, clear=True):
                self.assertEqual(build.release_version(root), "v0.0.2")
            with patch.dict(build.os.environ, {"PGRAZOR_VERSION": "v0.1.2"}, clear=True):
                self.assertEqual(build.release_version(root), "v0.1.2")
            with patch.dict(build.os.environ,
                            {"PGS_VERSION": "v0.0.3", "PGRAZOR_VERSION": "v0.1.2"},
                            clear=True):
                self.assertEqual(build.release_version(root), "v0.0.3")
            with patch.dict(build.os.environ, {"PGS_VERSION": "bad version"}, clear=True):
                with self.assertRaisesRegex(ValueError, "Invalid PGS version"):
                    build.release_version(root)


if __name__ == "__main__":
    unittest.main()
