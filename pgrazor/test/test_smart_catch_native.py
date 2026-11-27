"""Run the real smart-catch implementation and encounter validator on a Linux host."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

NATIVE = Path(__file__).resolve().parents[1] / 'native'
COMPILER = shutil.which('g++') or shutil.which('clang++')


@unittest.skipUnless(sys.platform.startswith('linux') and COMPILER,
                     'Native smart-catch fixtures require Linux/POSIX and g++ or clang++')
class SmartCatchNativeTests(unittest.TestCase):
    def compile_and_run(self, sources, expected):
        with tempfile.TemporaryDirectory(prefix='pgs-smart-catch-') as folder:
            executable = Path(folder) / 'fixture'
            build = subprocess.run(
                [COMPILER, '-O2', '-std=c++17', *[str(NATIVE / name) for name in sources],
                 '-ldl', '-o', str(executable)], capture_output=True, text=True, timeout=90)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            result = subprocess.run([str(executable)], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn(expected, result.stdout)

    def test_real_smart_catch_policy_and_gc_lifetime(self):
        self.compile_and_run(['smart_catch_test.cpp', 'smart_catch.cpp'],
                             'RPC identity, revocation and GC fixture passed')

    def test_real_encounter_response_validation(self):
        self.compile_and_run(['smart_encounter_validation_test.cpp'],
                             'PASS actual smart encounter validation')


if __name__ == '__main__':
    unittest.main()
