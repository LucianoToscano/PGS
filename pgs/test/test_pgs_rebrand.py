"""Safety regressions for the full-APK PGS Java-controls refresh."""
import io
import json
import sys
from pathlib import Path
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pgs_rebrand


class PgsRebrandTests(unittest.TestCase):
    def test_update_mode_preserves_native_runtime_configuration(self):
        original = {
            "gadget": False, "compiledGameplay": True,
            "pgrazorVersion": "v0.0.1",
            "runtimeAbis": ["arm64-v8a"],
            "nativePilot": True, "googleBrowserLogin": True,
        }
        result = json.loads(pgs_rebrand.updated_mode(
            json.dumps(original).encode("utf-8")))
        self.assertEqual(result["pgrazorVersion"], "v0.0.2")
        for key in original.keys() - {"pgrazorVersion"}:
            self.assertEqual(result[key], original[key])

    def test_refuse_wrong_gameplay_or_older_identity(self):
        for value in [
            {"pgrazorVersion": "v0.0.1", "compiledGameplay": False},
            {"pgrazorVersion": "v0.0.1"},
            {"pgrazorVersion": "v0.0.2", "compiledGameplay": True},
            {"pgrazorVersion": "v0.3.7", "compiledGameplay": True},
            {"pgrazorVersion": "v0.0.1", "compiledGameplay": "true"},
        ]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                pgs_rebrand.updated_mode(json.dumps(value).encode("utf-8"))

    def test_find_exactly_one_compiled_pgs_dex(self):
        with io.BytesIO() as data:
            with zipfile.ZipFile(data, "w") as apk:
                apk.writestr("classes.dex", b"dex\noriginal game data")
                apk.writestr("classes12.dex", b"dex\n" + pgs_rebrand.MARKER
                             + b"others" + pgs_rebrand.UPDATER)
            with zipfile.ZipFile(data) as apk:
                self.assertEqual(pgs_rebrand.module_dex_entry(apk), "classes12.dex")

    def test_reject_dex_ambiguity_and_missing_updater(self):
        for members in [
            [("classes.dex", b"dex\noriginal")],
            [("classes2.dex", pgs_rebrand.MARKER)],
            [("classes.dex", pgs_rebrand.MARKER + pgs_rebrand.UPDATER),
             ("classes2.dex", pgs_rebrand.MARKER + pgs_rebrand.UPDATER)],
        ]:
            with self.subTest(members=members):
                data = io.BytesIO()
                with zipfile.ZipFile(data, "w") as apk:
                    for name, contents in members:
                        apk.writestr(name, contents)
                with zipfile.ZipFile(data) as apk:
                    with self.assertRaises(ValueError):
                        pgs_rebrand.module_dex_entry(apk)

    def test_release_version_identity_never_confused_with_android_code(self):
        self.assertEqual(pgs_rebrand.PGS_VERSION, "v0.0.2")
        self.assertEqual(pgs_rebrand.TARGET_NAME, "PGS v0.0.2.apk")
        self.assertEqual(pgs_rebrand.SOURCE_VERSION_CODE, 2026111604)
        self.assertEqual(pgs_rebrand.TARGET_VERSION_CODE, 2026111605)
        self.assertEqual(pgs_rebrand.GAME_VERSION_NAME, "0.439.0")


if __name__ == "__main__":
    unittest.main()
