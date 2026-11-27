"""Compile the production IV panel fixture; simulated Canvas calls do not render Unity UI."""
from pathlib import Path
import sys
import shutil
import subprocess
import tempfile
import unittest

NATIVE = Path(__file__).resolve().parents[1] / 'native'
COMPILER = shutil.which('g++') or shutil.which('clang++')


@unittest.skipUnless(sys.platform.startswith('linux') and COMPILER,
                     'Native IV panel fixture requires Linux and g++ or clang++')
class IvPanelNativeTests(unittest.TestCase):
    def test_production_canvas_order_and_failure_paths(self):
        with tempfile.TemporaryDirectory(prefix='pgs-iv-panel-') as folder:
            executable = Path(folder) / 'iv-panel'
            build = subprocess.run(
                [COMPILER, '-O2', '-std=c++17', '-fexceptions', str(NATIVE / 'iv_panel_test.cpp'),
                 '-ldl', '-o', str(executable)], capture_output=True, text=True, timeout=90)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            result = subprocess.run([str(executable)], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('PASS IV panel production canvas', result.stdout)


if __name__ == '__main__':
    unittest.main()
