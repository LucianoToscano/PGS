"""Synthetic ZIP/ELF fixtures only: no signing key, game input, network or device."""
from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
import warnings
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pgs_candidate as candidate
import pgs_update


def elf(machine):
    return b"\x7fELF\x02\x01" + b"\0" * 12 + machine.to_bytes(2, "little") + b"\0" * 44


class PgsCandidateTests(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.addCleanup(self.work.cleanup)
        self.apk = Path(self.work.name) / "PGS.apk"
        self.identity = {
            "package": pgs_update.GAME_PACKAGE, "split": None, "applications": 1,
            "versionName": "0.439.0", "versionCode": 2026111607,
            "providers": [{"name": "dev.pgs.BootstrapProvider", "exported": False,
                           "authorities": pgs_update.GAME_PACKAGE + ".pgs.bootstrap"}],
            "activities": [],
        }
        self.mode = {"pgsVersion": "v0.0.4", "compiledGameplay": True,
                     "gadget": False, "runtimeAbis": ["arm64-v8a", "x86_64"]}
        self.members = {
            "AndroidManifest.xml": b"synthetic manifest",
            "resources.arsc": b"synthetic resources",
            "classes.dex": b"dex\noriginal game fixture",
            "classes2.dex": b"dex\n" + b"\0".join(candidate.REQUIRED_CLASSES),
            "lib/arm64-v8a/libil2cpp.so": elf(183),
        }
        for abi, machine in candidate.MACHINES.items():
            for name in ("libpgs-core.so", "libpgs-art.so"):
                self.members[f"assets/pgs/{abi}/{name}"] = elf(machine)
        for target, value in (
            ("MIN_APK_BYTES", 0),
            ("axml.inspect_manifest", None),
            ("axml._parse", None),
            ("axml._walk", None),
            ("pgs_update.cert_digests", None),
            ("build.android_tool", None),
            ("nonroot.command", None),
        ):
            if value is not None:
                mock = patch("pgs_candidate." + target, value)
            else:
                mock = patch("pgs_candidate." + target)
            obj = mock.start()
            self.addCleanup(mock.stop)
            if target == "axml.inspect_manifest":
                obj.return_value = self.identity
            elif target == "axml._parse":
                obj.return_value = (None, [], None, None, None)
            elif target == "axml._walk":
                obj.return_value = [(0, "start", "application",
                                     {(candidate.axml.ANDROID_NS, "label"): "Pok\u00e9mon GO"}, 1)]
            elif target == "pgs_update.cert_digests":
                self.signer = obj
                obj.return_value = [pgs_update.PGS_SIGNER]

    def write(self, duplicate=False):
        with zipfile.ZipFile(self.apk, "w") as archive:
            archive.writestr(candidate.MODE, json.dumps(self.mode))
            for name, data in self.members.items():
                archive.writestr(name, data)
            if duplicate:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    archive.writestr("classes.dex", b"duplicate")

    def verify(self):
        return candidate.verify(self.apk, tag="v0.0.4", game_version="0.439.0",
                                game_version_code=2026111602, previous_version_code=2026111606)

    def test_complete_static_candidate_never_claims_installation(self):
        self.write()
        before = self.apk.read_bytes()
        report = self.verify()
        self.assertEqual(report["version_code"], 2026111607)
        self.assertEqual(report["release_asset"], "PGS.v0.0.4.apk")
        self.assertFalse(report["device_tested"])
        self.assertFalse(report["in_place_update_tested"])
        self.assertFalse(report["publish_ready"])
        self.assertEqual(self.apk.read_bytes(), before)

    def test_reject_missing_pgs_version(self):
        self.mode.pop("pgsVersion")
        self.write()
        with self.assertRaisesRegex(ValueError, "mode version"):
            self.verify()

    def test_reject_small_preview(self):
        self.write()
        with patch.object(candidate, "MIN_APK_BYTES", 100_000_000):
            with self.assertRaisesRegex(ValueError, "Incomplete APK"):
                self.verify()

    def test_reject_foreign_certificate(self):
        self.write()
        self.signer.return_value = ["foreign"]
        with self.assertRaisesRegex(ValueError, "certificate mismatch"):
            self.verify()

    def test_reject_stale_version_code(self):
        self.identity["versionCode"] = 2026111605
        self.write()
        with self.assertRaisesRegex(ValueError, "versionCode"):
            self.verify()

    def test_reject_legacy_controls_dex(self):
        self.members["classes3.dex"] = b"dex\nLdev/pgrazor/Control;"
        self.write()
        with self.assertRaisesRegex(ValueError, "Legacy controls"):
            self.verify()

    def test_reject_missing_library(self):
        del self.members["assets/pgs/arm64-v8a/libpgs-art.so"]
        self.write()
        with self.assertRaisesRegex(ValueError, "Missing PGS library"):
            self.verify()

    def test_reject_wrong_elf_abi(self):
        self.members["assets/pgs/arm64-v8a/libpgs-core.so"] = elf(62)
        self.write()
        with self.assertRaisesRegex(ValueError, "ELF architecture"):
            self.verify()

    def test_reject_enabled_experimental_oauth(self):
        self.mode["googleBrowserLogin"] = True
        self.write()
        with self.assertRaisesRegex(ValueError, "googleBrowserLogin enabled but GoogleAuthActivity not declared"):
            self.verify()

    def test_reject_oauth_callback(self):
        self.mode["googleBrowserLogin"] = True
        self.identity["activities"] = [{"name": "dev.pgs.GoogleAuthActivity", "exported": True}]
        self.write()
        with self.assertRaisesRegex(ValueError, "Unexpected Google browser callback filter"):
            self.verify()

    def test_reject_duplicate_zip_entries(self):
        self.write(duplicate=True)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.verify()


if __name__ == "__main__":
    unittest.main()
