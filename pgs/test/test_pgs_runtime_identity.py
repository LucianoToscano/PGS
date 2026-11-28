"""Verify that the Java/JNI, binary and asset layout migrates as one contract."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parent
sys.path.insert(0, str(PROJECT))
import axml
import art_build
import native_build
import nonroot
import pgs_rebrand
import pgs_update
import rooted


class PgsRuntimeIdentityTests(unittest.TestCase):
    def test_java_namespace_and_jni_registration(self):
        paths = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode("utf-8").split("\0")
        self.assertTrue(any(p.startswith("pgs/src/dev/pgs/") for p in paths))
        for path in (PROJECT / "src/dev/pgs").rglob("*.java"):
            self.assertIn("package dev.pgs", path.read_text(encoding="utf-8", errors="surrogateescape"), path.name)
        for file, target in (
            ("native/jni_core.cpp", "NativeCore"),
            ("native/runtime_transport_jni.cpp", "NativeRuntimeTransport"),
            ("art/java_hooks.cpp", "NativeJavaHooks"),
        ):
            content = (PROJECT / file).read_text(encoding="utf-8")
            self.assertIn('"dev/pgs/' + target + '"', content)
            self.assertIn("RegisterNatives", content)
        self.assertEqual(axml.PROVIDER, "dev.pgs.BootstrapProvider")

    def test_library_and_asset_names_match_packagers_and_loaders(self):
        self.assertEqual(native_build.OUTPUT_SONAME, "libpgs-core.so")
        self.assertEqual(art_build.SONAME, "libpgs-art.so")
        for name in ("libpgs-core.so", "libpgs-art.so"):
            self.assertIn(name, (PROJECT / "nonroot.py").read_text(encoding="utf-8"))
            self.assertIn(name, (PROJECT / "src/dev/pgs/BootstrapProvider.java").read_text(encoding="utf-8"))
            self.assertIn(name, (PROJECT / "rooted.py").read_text(encoding="utf-8"))
        loader = (PROJECT / "zygisk/loader.cpp").read_text(encoding="utf-8")
        self.assertIn('"pgs/classes.dex"', loader)
        self.assertIn('"pgs/payload.zip"', loader)
        self.assertIn('"dev.pgs.RootedEntry"', loader)
        self.assertEqual(rooted.MODULE_ID, "pgs")
        self.assertEqual(rooted.INJECTION_OFF_FLAG, "pgs/injection-off")

    def test_standalone_preview_package_is_pgs(self):
        import xml.etree.ElementTree as ET
        manifest = ET.parse(PROJECT / "AndroidManifest.xml").getroot()
        self.assertEqual(manifest.get("package"), "dev.pgs.preview")
        source = (PROJECT / "nonroot.py").read_text(encoding="utf-8")
        self.assertIn("package_name!='dev.pgs.preview'", source)
        self.assertIn("report['package']!='dev.pgs.preview'", source)
        self.assertIn("'dev.pgs.preview/dev.pgs.PreviewActivity'", source)
        self.assertIn("'am','force-stop','dev.pgs.preview'", source)
        # Clean install: only the current PGS preview package is recognised.
        cleanup = (PROJECT / "cleanup.ps1").read_text(encoding="utf-8-sig")
        self.assertIn("'dev.pgs.preview'", cleanup)
        # Wrong package is rejected as non-preview.
        with self.assertRaisesRegex(RuntimeError, "restricted to our standalone preview"):
            nonroot.probe({"package": "com.nianticlabs.pokemongo", "outputs": [{}]}, PROJECT, None)
        # Correct preview package but no attached device is rejected.
        with self.assertRaisesRegex(RuntimeError, "requires an attached Android device"):
            nonroot.probe({"package": "dev.pgs.preview", "outputs": [{}]}, PROJECT, None)

    def test_new_root_cache_is_pgs_without_retiring_installed_off_switch(self):
        runtime = (PROJECT / "src/dev/pgs/RootedRuntime.java").read_text(encoding="utf-8")
        self.assertIn('new File(new File(dataDir, "code_cache"), "pgs-root")', runtime)
        # The fixed installed module identity and user-selected Off flag are separate contracts.
        self.assertEqual(rooted.MODULE_ID, "pgs")
        self.assertEqual(rooted.INJECTION_OFF_FLAG, "pgs/injection-off")

    def test_reject_both_legacy_and_new_patched_input(self):
        for asset in ("assets/pgs/mode.json",):
            with self.subTest(asset=asset), tempfile.TemporaryDirectory() as folder:
                source = Path(folder) / "synthetic.apk"
                with zipfile.ZipFile(source, "w") as archive:
                    archive.writestr(asset, b"{}")
                with self.assertRaisesRegex(ValueError, "already has PGS assets"):
                    nonroot.rewrite_apk(source, Path(folder) / "output.apk", base=True)
        for marker in (b"Ldev/pgs/Control;",):
            with self.subTest(marker=marker), tempfile.TemporaryDirectory() as folder:
                source = Path(folder) / "synthetic.apk"
                with zipfile.ZipFile(source, "w") as archive:
                    archive.writestr("classes.dex", b"dex\n" + marker)
                with self.assertRaisesRegex(ValueError, "already contains PGS classes"):
                    nonroot.rewrite_apk(source, Path(folder) / "output.apk", base=True)

    def test_dex_bridge_uses_pgs_prefix_and_rejects_legacy_input(self):
        bridge = (ROOT / "tools/dex_bridge/BridgeRewriter.java").read_text(encoding="utf-8")
        self.assertIn('PREFIX="$pgs$original$"', bridge)
        self.assertIn('!m.getName().startsWith(PREFIX)', bridge)

    def test_installed_identity_and_historical_repack_are_preserved(self):
        self.assertEqual(pgs_update.GAME_PACKAGE, "com.nianticlabs.pokemongo")
        self.assertEqual(pgs_update.PGS_SIGNER, "d95c6bdfcbd91dc5c9cde698487c88e4994771a475e4efde4567b8d5f44e96cf")
        self.assertEqual(pgs_rebrand.MARKER, b"Ldev/pgs/Control;")
        self.assertEqual(pgs_rebrand.MODE, "assets/pgs/mode.json")
        self.assertEqual(pgs_rebrand.TARGET_VERSION_CODE, 2026111605)
        # The v0.0.1 historical release workflow refuses rebuilds from newer PGS sources.
        v001 = (ROOT / ".github/workflows" / "pgs-v0.0.1-release.yml").read_text(encoding="utf-8")
        self.assertIn("v0.0.1 is historical", v001)
        self.assertIn("use the v0.0.2 release workflow", v001)
        # The v0.0.2 and same-package-update workflows are legitimate PGS release flows.
        for name in ("pgs-v0.0.2-release.yml", "pgs-same-package-update.yml"):
            flow = (ROOT / ".github/workflows" / name).read_text(encoding="utf-8")
            self.assertIn("PGS", flow)


if __name__ == "__main__":
    unittest.main()
