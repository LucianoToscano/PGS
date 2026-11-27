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
                         frozenset({"JNI_OnLoad", "pgs_native_api"}))
        self.assertTrue((NATIVE / "pgs_native.cpp").is_file())
        self.assertFalse((NATIVE / "pgrazor_native.cpp").exists())
        self.assertFalse((NATIVE / "pgrazor.map").exists())
        exports = (NATIVE / "pgs.map").read_text(encoding="utf-8")
        self.assertNotIn("pgrazor_native_api;", exports)
        self.assertIn("pgs_native_api;", exports)

    def test_pgs_header_is_primary_and_legacy_abi_removed(self):
        header = (NATIVE / "pgs_native_api.h").read_text(encoding="utf-8")
        shim = (NATIVE / "pgs_native_api_compat.h").read_text(encoding="utf-8")
        self.assertFalse((NATIVE / "pgrazor_native_api.h").exists())
        internal = (NATIVE / "pgs_internal.h").read_text(encoding="utf-8")
        self.assertNotIn("typedef pgs_native_api_v2 pgrazor_native_api_v2;", header)
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
        self.assertNotIn("pgrazor_native_api(uint32_t version)", core)
        self.assertNotIn("return pgs_native_api(version);", core)
        self.assertIn("const void *pgs_native_api(uint32_t version);", header)
        self.assertNotIn("const void *pgrazor_native_api(uint32_t version);", header)
        self.assertIn("#define PGS_NATIVE_API_VERSION 1u", header)
        self.assertIn("PGS_ERR_BAD_LEASE = 4", header)

    def test_art_target_and_output_use_pgs(self):
        cmake = (ART / "CMakeLists.txt").read_text(encoding="utf-8")
        self.assertIn("project(pgs_art LANGUAGES C CXX)", cmake)
        self.assertIn("add_library(pgs_art SHARED", cmake)
        self.assertIn("pgs-art.map", cmake)
        self.assertIn('OUTPUT_NAME "pgs-art"', cmake)
        self.assertTrue((ART / "pgs-art.map").is_file())
        self.assertFalse((ART / "pgrazor-art.map").exists())
        # These are JNI/LSPlant integration hooks, not cosmetic CMake target names.
        hooks = (ART / "java_hooks.cpp").read_text(encoding="utf-8")
        for suffix in ("begin", "end"):
            self.assertIn("pgs_art_publication_" + suffix, cmake)
            self.assertIn("pgs_art_publication_" + suffix, hooks)
            self.assertNotIn("pgrazor_art_publication_" + suffix, cmake)
            self.assertNotIn("pgrazor_art_publication_" + suffix, hooks)
        self.assertIn("PGS_ART_CHAIN_TEST", cmake)
        self.assertNotIn("PGRAZOR_ART_CHAIN_TEST", cmake)
        self.assertEqual(art_build.SONAME, "libpgs-art.so")

    def test_new_build_options_use_pgs_names_only(self):
        self.assertEqual(native_build._PILOT_ENV, "PGS_NATIVE_PILOT")
        self.assertEqual(native_build._DOWNLOAD_ENV, "PGS_NATIVE_DOWNLOAD")
        self.assertFalse(native_build._enabled("PGS_NATIVE_PILOT", {}))
        self.assertTrue(native_build._enabled("PGS_NATIVE_PILOT", {"PGS_NATIVE_PILOT": "1"}))
        self.assertFalse(native_build._enabled("PGS_NATIVE_PILOT", {"PGS_NATIVE_PILOT": "0"}))

    def test_first_party_native_sources_no_longer_include_old_api_header(self):
        old = b'#include "pgrazor_native_api.h"'
        offenders = []
        for source in NATIVE.rglob("*"):
            if source.is_file() and source.suffix in {".cpp", ".cc", ".c", ".h", ".hpp", ".inc"}:
                if old in source.read_bytes():
                    offenders.append(str(source.relative_to(ROOT)))
        self.assertEqual(offenders, [],
                         "All native sources must include pgs_native_api.h; compatibility symbols remain available")


    def test_hook_engine_pgs_names_and_retired_cpp_linkage(self):
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
            self.assertNotIn("int " + legacy, impl)
            self.assertNotIn("int " + legacy, header)
            self.assertNotIn("int " + legacy, diag)
        self.assertIn("struct PgsHookDiag {", diag)
        self.assertIn("struct PgsPaddingRanges {", header)
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

    def test_primary_account_abbreviations(self):
        header = (NATIVE / "accounts.h").read_text(encoding="utf-8")
        compat = (NATIVE / "account_source_compat.h").read_text(encoding="utf-8")
        self.assertIn("#ifndef PGS_ACCOUNTS_H_", header)
        self.assertIn("#define PGS_FEATURE_ACCOUNTS 16u", header)
        self.assertIn("PGS_ACC_CMD_NONE = 0", header)
        self.assertIn("PGS_ACCOUNTS_API_TABLE_SIZE 56u", header)
        self.assertNotIn("#define PGR_FEATURE_ACCOUNTS", header)
        self.assertNotIn("PGR_ACC_CMD_NONE = ", header)
        self.assertNotIn('#include "account_source_compat.h"', header)
        self.assertNotRegex(compat, r"\bPGR_[A-Z0-9_]+")
        account = (NATIVE / "account_host.cpp").read_bytes()
        self.assertNotRegex(account, rb"\b(?:PGR_|pgr_|Pgr[A-Z])")
        self.assertIn(b"PGS_ACC_CMD_NONE", account)

    def test_primary_native_factory_consumers(self):
        camera = (NATIVE / "camera_host.cpp").read_text(encoding="utf-8")
        spawn = (NATIVE / "spawn_host.cpp").read_text(encoding="utf-8")
        primary = 'dlsym(g_state.core_handle, "pgs_native_api")'
        self.assertIn(primary, camera)
        self.assertIn("*>(pgs_native_api(2u))", camera)
        self.assertIn("return pgs_hook(target, replacement, original);", camera)
        self.assertIn("*>(pgs_native_api(1))", spawn)
        self.assertNotIn("pgrazor_native_api", camera)
        self.assertNotIn("pgrazor_native_api", spawn)

    def test_pgs_cmd_is_primary_and_legacy_launcher_forwards(self):
        primary = (ROOT / "pgs.cmd").read_text(encoding="utf-8")
        legacy = (ROOT / "nonroot.cmd").read_text(encoding="utf-8")
        self.assertIn("PGS_PYTHON", primary)
        self.assertNotIn("PGRAZOR_PYTHON", primary)
        self.assertIn("pgs.cmd", legacy)
        self.assertIn("nonroot.py", primary)


if __name__ == "__main__":
    unittest.main()
