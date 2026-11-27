"""Exercise the real IV refresh module with its existing fake managed heap and hook dispatch."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

NATIVE = Path(__file__).resolve().parents[1] / 'native'
COMPILER = shutil.which('g++') or shutil.which('clang++')


@unittest.skipUnless(sys.platform.startswith('linux') and COMPILER,
                     'Native IV refresh fixture requires Linux/POSIX and g++ or clang++')
class IvOwnedRefreshNativeTests(unittest.TestCase):
    def test_real_refresh_lifetime_and_authorization(self):
        with tempfile.TemporaryDirectory(prefix='pgs-iv-refresh-') as folder:
            folder = Path(folder)
            # hook_engine.h mentions this Dobby callback type, unused by iv_display.cpp.
            # The fixture supplies pgrazor_hook dispatch; no instruction patching is claimed.
            (folder / 'dobby.h').write_text(
                '#pragma once\ntypedef void (*dobby_instrument_callback_t)(void*, void*);\n', encoding='utf-8')
            executable = folder / 'iv-refresh'
            build = subprocess.run(
                [COMPILER, '-O2', '-std=c++17', '-I'+str(folder),
                 str(NATIVE / 'iv_owned_refresh_test.cpp'), str(NATIVE / 'iv_display.cpp'),
                 '-ldl', '-pthread', '-o', str(executable)], capture_output=True, text=True, timeout=90)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            result = subprocess.run([str(executable)], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('PASS owned IV refresh', result.stdout)

    def test_legacy_iv_display_scenarios_with_simulated_hook_dispatch(self):
        """Run the existing default/shared observer scenarios against the real module.

        Only hook registration and the feature registry are simulated; this does not
        validate Dobby instruction patching or the Android/Unity runtime.
        """
        with tempfile.TemporaryDirectory(prefix='pgs-iv-legacy-') as folder:
            folder = Path(folder)
            (folder / 'dobby.h').write_text(
                '#pragma once\ntypedef void (*dobby_instrument_callback_t)(void*, void*);\n', encoding='utf-8')
            shim = folder / 'registry.cpp'
            shim.write_text('''
#include "iv_display.h"
#include "pgrazor_native_api.h"
extern "C" int fixture_hook_dispatch(void *, void *, void **);
int pgrazor_hook(void *address, void *replacement, void **original) {
    return fixture_hook_dispatch(address, replacement, original);
}
extern "C" const void *pgrazor_runtime_bootstrap_api(uint32_t) { return nullptr; }
const void *fixture_query(uint32_t feature, uint32_t version) {
    return feature == 15 ? pgrazor_iv_display_api(version) : nullptr;
}
extern "C" const void *pgrazor_native_api(uint32_t version) {
    static const pgrazor_native_api_v2 api{2, sizeof(pgrazor_native_api_v2),
        nullptr, nullptr, nullptr, nullptr, fixture_query};
    return version == 2 ? &api : nullptr;
}
''', encoding='utf-8')
            fixture = folder / 'legacy.cpp'
            fixture.write_text('''
#include "iv_display_test.cpp"
extern "C" int fixture_hook_dispatch(void *address, void *replacement, void **original) {
    *original = address;
    if (address == (void *)target_owned)
        call_owned = reinterpret_cast<decltype(call_owned)>(replacement);
    else if (address == (void *)target_setup)
        call_setup = reinterpret_cast<decltype(call_setup)>(replacement);
    else return -1;
    return 0;
}
''', encoding='utf-8')
            library = folder / 'libiv-fixture.so'
            executable = folder / 'iv-legacy'
            flags = [COMPILER, '-O2', '-std=c++17', '-I'+str(folder), '-I'+str(NATIVE)]
            commands = [
                flags + ['-shared', '-fPIC', str(shim), str(NATIVE / 'iv_display.cpp'),
                         '-ldl', '-pthread', '-o', str(library)],
                flags + ['-rdynamic', str(fixture), '-ldl', '-pthread', '-o', str(executable)],
            ]
            for command in commands:
                build = subprocess.run(command, capture_output=True, text=True, timeout=90)
                self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            result = subprocess.run([str(executable), str(library)],
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('iv_display_test passed:', result.stdout)


if __name__ == '__main__':
    unittest.main()
