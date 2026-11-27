"""Exercise real native item catalog and host policy with simulated external APIs.

The item fixture simulates its managed heap and replaces hooks/time; the policy
fixture links inventory_host.cpp and observes its calls to leaf API spies.
Neither fixture changes a live game or verifies Android instruction patching.
"""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

NATIVE = Path(__file__).resolve().parents[1] / 'native'
COMPILER = shutil.which('g++') or shutil.which('clang++')


@unittest.skipUnless(sys.platform.startswith('linux') and COMPILER,
                     'Native inventory fixtures require Linux and a C++17 compiler')
class InventoryBerriesNativeTests(unittest.TestCase):
    def compile_and_run(self, sources, flags, expected):
        with tempfile.TemporaryDirectory(prefix='pgs-inventory-') as folder:
            folder = Path(folder)
            (folder / 'dobby.h').write_text(
                '#pragma once\ntypedef void (*dobby_instrument_callback_t)(void*, void*);\n',
                encoding='utf-8')
            executable = folder / 'fixture'
            built = subprocess.run([
                COMPILER, '-std=c++17', '-O2', '-pthread', '-I' + str(folder),
                *flags, *[str(NATIVE / source) for source in sources],
                '-ldl', '-o', str(executable),
            ], text=True, capture_output=True, timeout=60)
            self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
            result = subprocess.run([str(executable)], text=True,
                                    capture_output=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn(expected, result.stdout)

    def test_real_items_catalog_and_berry_counts(self):
        self.compile_and_run(
            ['items.cpp', 'items_test.cpp'],
            ['-DPGR_ITEMS_HOST_TEST', '-Wl,--wrap=clock_gettime,--wrap=nanosleep'],
            'PASS native items:')

    def test_real_inventory_host_buddy_policy(self):
        self.compile_and_run(
            ['inventory_host.cpp', 'inventory_berries_policy_test.cpp'], [],
            'PASS inventory berry policy: Silver Pinap708')


if __name__ == '__main__':
    unittest.main()
