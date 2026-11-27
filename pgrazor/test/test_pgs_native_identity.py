"""PGS native build identity, names and ABI compatibility regression."""
from pathlib import Path
import unittest
import native_build
import art_build

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "native"
ART = ROOT / "art"


class PgsNativeRenameTests(unittest.TestCase):
    def test_new_native_build_names_keep_installed_binary_contract(self):
        cmake = (NATIVE / "CMakeLists.txt").read_text(encoding="utf-8")
        self.assertIn("project(pgs_core LANGUAGES C CXX)", cmake)
        self.assertIn("add_library(pgs_core SHARED", cmake)
        self.assertIn("pgs_native.cpp", cmake)
        self.assertIn("PGS_VERSION_SCRIPT", cmake)
        self.assertIn("/pgs.map", cmake)
        self.assertIn('OUTPUT_NAME "pgrazor-core"', cmake)
        self.assertEqual(native_build.TARGET, "pgs_core")
        self.assertEqual(native_build.OUTPUT_SONAME, "libpgrazor-core.so")
        self.assertEqual(native_build.EXPECTED_EXPORTS,
                         frozenset({"JNI_OnLoad", "pgrazor_native_api"}))
        self.assertTrue((NATIVE / "pgs_native.cpp").is_file())
        self.assertFalse((NATIVE / "pgrazor_native.cpp").exists())
        self.assertFalse((NATIVE / "pgrazor.map").exists())
        self.assertIn("pgrazor_native_api;", (NATIVE / "pgs.map").read_text(encoding="utf-8"))

    def test_pgs_header_is_primary_and_old_includes_remain_valid(self):
        header = (NATIVE / "pgs_native_api.h").read_text(encoding="utf-8")
        shim = (NATIVE / "pgrazor_native_api.h").read_text(encoding="utf-8")
        internal = (NATIVE / "pgs_internal.h").read_text(encoding="utf-8")
        self.assertIn("typedef pgrazor_native_api_v2 pgs_native_api_v2;", header)
        self.assertIn('#include "pgs_native_api.h"', shim)
        self.assertIn("int pgs_policy_selfcheck(void);", internal)
        self.assertFalse((NATIVE / "pgrazor_internal.h").exists())
        core = (NATIVE / "pgs_native.cpp").read_text(encoding="utf-8")
        glue = (NATIVE / "jni_core.cpp").read_text(encoding="utf-8")
        for content in (core, glue):
            self.assertIn('#include "pgs_native_api.h"', content)
            self.assertIn('#include "pgs_internal.h"', content)
            self.assertIn("pgs_policy_selfcheck", content)
        self.assertIn("pgrazor_native_api(uint32_t version)", core)

    def test_art_target_is_pgs_but_abi_output_unchanged(self):
        cmake = (ART / "CMakeLists.txt").read_text(encoding="utf-8")
        self.assertIn("project(pgs_art LANGUAGES C CXX)", cmake)
        self.assertIn("add_library(pgs_art SHARED", cmake)
        self.assertIn("pgs-art.map", cmake)
        self.assertIn('OUTPUT_NAME "pgrazor-art"', cmake)
        self.assertTrue((ART / "pgs-art.map").is_file())
        self.assertFalse((ART / "pgrazor-art.map").exists())
        # These are JNI/LSPlant integration hooks, not cosmetic CMake target names.
        self.assertIn("pgrazor_art_publication_begin", cmake)
        self.assertIn("PGS_ART_CHAIN_TEST", cmake)
        self.assertIn("PGRAZOR_ART_CHAIN_TEST", cmake)
        self.assertEqual(art_build.SONAME, "libpgrazor-art.so")

    def test_new_build_options_accept_preexisting_environment_aliases(self):
        self.assertEqual(native_build._PILOT_ENV, "PGS_NATIVE_PILOT")
        self.assertEqual(native_build._DOWNLOAD_ENV, "PGS_NATIVE_DOWNLOAD")
        self.assertFalse(native_build._enabled("PGS_NATIVE_PILOT", "PGRAZOR_NATIVE_PILOT", {}))
        self.assertTrue(native_build._enabled("PGS_NATIVE_PILOT", "PGRAZOR_NATIVE_PILOT",
                                              {"PGS_NATIVE_PILOT": "1"}))
        self.assertTrue(native_build._enabled("PGS_NATIVE_PILOT", "PGRAZOR_NATIVE_PILOT",
                                              {"PGRAZOR_NATIVE_PILOT": "1"}))
        self.assertFalse(native_build._enabled("PGS_NATIVE_PILOT", "PGRAZOR_NATIVE_PILOT",
                                               {"PGS_NATIVE_PILOT": "0", "PGRAZOR_NATIVE_PILOT": "0"}))

    def test_pgs_cmd_is_primary_and_legacy_launcher_forwards(self):
        primary = (ROOT / "pgs.cmd").read_text(encoding="utf-8")
        legacy = (ROOT / "nonroot.cmd").read_text(encoding="utf-8")
        self.assertIn("PGS_PYTHON", primary)
        self.assertIn("PGRAZOR_PYTHON", primary)
        self.assertIn("pgs.cmd", legacy)
        self.assertIn("nonroot.py", primary)


if __name__ == "__main__":
    unittest.main()
