"""PGS native build identity, names and ABI compatibility regression."""
from pathlib import Path
import re
import unittest
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import native_build
import art_build

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "native"
ART = ROOT / "art"


class PgsNativeRenameTests(unittest.TestCase):
    def test_new_native_build_names_keep_exported_binary_contract(self):
        cmake = (NATIVE / "CMakeLists.txt").read_text(encoding="utf-8")
        self.assertIn("project(pgs_core LANGUAGES C CXX)", cmake)
        self.assertIn("add_library(pgs_core SHARED", cmake)
        self.assertIn("pgs_native.cpp", cmake)
        self.assertIn("PGS_VERSION_SCRIPT", cmake)
        self.assertIn("/pgs.map", cmake)
        self.assertIn('OUTPUT_NAME "pgs-core"', cmake)
        self.assertEqual(native_build.TARGET, "pgs_core")
        self.assertEqual(native_build.OUTPUT_SONAME, "libpgs-core.so")
        self.assertEqual(native_build.EXPECTED_EXPORTS,
                         frozenset({"JNI_OnLoad", "pgs_native_api", "pgrazor_native_api"}))
        self.assertTrue((NATIVE / "pgs_native.cpp").is_file())
        self.assertFalse((NATIVE / "pgrazor_native.cpp").exists())
        self.assertFalse((NATIVE / "pgrazor.map").exists())
        exports = (NATIVE / "pgs.map").read_text(encoding="utf-8")
        self.assertIn("pgrazor_native_api;", exports)
        self.assertIn("pgs_native_api;", exports)

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
        self.assertIn("pgs_native_api(uint32_t version)", core)
        self.assertIn("pgrazor_native_api(uint32_t version)", core)
        self.assertIn("return pgs_native_api(version);", core)
        self.assertIn("const void *pgs_native_api(uint32_t version);", header)
        self.assertIn("const void *pgrazor_native_api(uint32_t version);", header)
        self.assertIn("#define PGRAZOR_NATIVE_API_VERSION PGS_NATIVE_API_VERSION", header)
        self.assertIn("#define PGRAZOR_ERR_BAD_LEASE PGS_ERR_BAD_LEASE", header)

    def test_art_target_and_output_use_pgs(self):
        cmake = (ART / "CMakeLists.txt").read_text(encoding="utf-8")
        self.assertIn("project(pgs_art LANGUAGES C CXX)", cmake)
        self.assertIn("add_library(pgs_art SHARED", cmake)
        self.assertIn("pgs-art.map", cmake)
        self.assertIn('OUTPUT_NAME "pgs-art"', cmake)
        self.assertTrue((ART / "pgs-art.map").is_file())
        self.assertFalse((ART / "pgrazor-art.map").exists())
        # These are JNI/LSPlant integration hooks, not cosmetic CMake target names.
        self.assertIn("pgrazor_art_publication_begin", cmake)
        self.assertIn("PGS_ART_CHAIN_TEST", cmake)
        self.assertIn("PGRAZOR_ART_CHAIN_TEST", cmake)
        self.assertEqual(art_build.SONAME, "libpgs-art.so")

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

    def test_first_party_native_sources_no_longer_include_old_api_header(self):
        old = b'#include "pgrazor_native_api.h"'
        offenders = []
        for source in NATIVE.rglob("*"):
            if source.is_file() and source.suffix in {".cpp", ".cc", ".c", ".h", ".hpp", ".inc"}:
                if old in source.read_bytes():
                    offenders.append(str(source.relative_to(ROOT)))
        self.assertEqual(offenders, [],
                         "All native sources must include pgs_native_api.h; old shim is for compatibility only")


    def test_hook_engine_pgs_names_and_old_cpp_linkage(self):
        header = (NATIVE / "hook_engine.h").read_text(encoding="utf-8")
        diag = (NATIVE / "hook_engine_diag.h").read_text(encoding="utf-8")
        impl = (NATIVE / "hook_engine.cpp").read_text(encoding="utf-8")
        core = (NATIVE / "pgs_native.cpp").read_text(encoding="utf-8")
        for prefix in ("pgs_hook(", "pgs_unhook(", "pgs_instrument("):
            self.assertIn("int " + prefix, header)
            self.assertIn("int " + prefix, impl)
        for legacy, modern in (
            ("pgrazor_hook(", "pgs_hook("),
            ("pgrazor_unhook(", "pgs_unhook("),
            ("pgrazor_instrument(", "pgs_instrument("),
            ("pgrazor_hook_diag(", "pgs_hook_diag("),
        ):
            self.assertIn("int " + legacy, impl)
            self.assertIn("return " + modern, impl)
        self.assertIn("using PgsHookDiag = PgrHookDiag;", diag)
        self.assertIn("using PgsPaddingRanges = PgrPaddingRanges;", header)
        self.assertNotIn('"PGRazor"', impl)
        self.assertIn("pgs_hook(", core)
        self.assertIn("pgs_unhook(", core)
        self.assertNotIn("pgrazor_hook(", core)

    def test_phase6_hook_consumers_and_host_fixtures_use_pgs_name(self):
        for name, expected in (("buddy_feeding", 2), ("items", 5)):
            with self.subTest(module=name):
                source = (NATIVE / (name + ".cpp")).read_text(encoding="utf-8")
                fixture = (NATIVE / (name + "_test.cpp")).read_text(encoding="utf-8")
                self.assertNotIn("pgrazor_hook(", source)
                self.assertNotIn("pgrazor_hook(", fixture)
                self.assertEqual(source.count("pgs_hook("), expected)
                self.assertIn("int pgs_hook(", fixture)

    def test_phase7_iv_and_inventory_hook_consumers_use_pgs_name(self):
        for name, expected in (("iv_display.cpp", 2), ("inventory_host.cpp", 1)):
            with self.subTest(module=name):
                source = (NATIVE / name).read_text(encoding="utf-8")
                self.assertNotIn("pgrazor_hook(", source)
                self.assertEqual(source.count("pgs_hook("), expected)
        for path in (NATIVE / "iv_owned_refresh_test.cpp",
                     NATIVE / "inventory_berries_policy_test.cpp",
                     ROOT / "test" / "test_iv_owned_refresh_native.py"):
            with self.subTest(fixture=path.name):
                fixture = path.read_text(encoding="utf-8")
                self.assertNotIn("pgrazor_hook(", fixture)
                self.assertIn("int pgs_hook(", fixture)

    def test_phase9_bulk_direct_hook_consumers_use_pgs_symbols(self):
        names = (
            "auto_raid.cpp",
            "menu_visibility.cpp",
            "profile_scroll.cpp",
            "routes_tracking.cpp",
            "catch_presentation.cpp",
            "transfer_observers.cpp",
            "adventure_sync.cpp",
            "always_hit.cpp",
            "unity_scheduler.cpp",
            "route_gift.cpp",
            "map_tap.cpp",
            "throws.cpp",
            "ar_throw.cpp",
            "quick_spin.cpp",
            "rocket_swap.cpp",
            "catch_wait.cpp",
            "battery.cpp",
            "shundo.cpp",
            "routes_services.cpp",
            "catch_canvas.cpp",
            "routes_observers.cpp",
            "accounts.cpp",
            "spin_camera.cpp",
            "storage_iv.cpp",
            "catch_observers.cpp",
            "gym_repeat.cpp",
            "rocket_minigame.cpp",
            "smart_battle.cpp",
            "shared_host.cpp",
            "combat_host.cpp",
            "cutscene_skip.cpp",
            "events/event_collector.cpp",
            "map_auto_throw_game.inc",
            "encounter_host.cpp",
            "safari_throws_test.cpp",
            "profile_scroll_test.cpp",
            "safari_always_hit_test.cpp",
            "menu_visibility_test.cpp",
            "tests/accounts_test.cpp",
            "cutscene_skip_test.cpp",
            "gym_repeat_runtime_test.cpp",
            "auto_raid_runtime_test.cpp",
            "events/event_collector_test.cpp",
            "tests/accounts_dobby_bridge.cpp",
            "unity_scheduler_diag_test.cpp",
            "shared_host_flow_test.cpp",
        )
        legacy = re.compile(r'\bpgrazor_(?:hook|unhook|instrument|hook_diag)\b')
        primary = re.compile(r'\bpgs_(?:hook|unhook|instrument|hook_diag)\b')
        for name in names:
            with self.subTest(path=name):
                content = (NATIVE / name).read_text(encoding='utf-8')
                self.assertIsNone(legacy.search(content))
                self.assertIsNotNone(primary.search(content))

    def test_pgs_cmd_is_primary_and_legacy_launcher_forwards(self):
        primary = (ROOT / "pgs.cmd").read_text(encoding="utf-8")
        legacy = (ROOT / "nonroot.cmd").read_text(encoding="utf-8")
        self.assertIn("PGS_PYTHON", primary)
        self.assertIn("PGRAZOR_PYTHON", primary)
        self.assertIn("pgs.cmd", legacy)
        self.assertIn("nonroot.py", primary)


if __name__ == "__main__":
    unittest.main()
