"""Exercise the production graphics ownership policy with a host C++17 compiler."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

NATIVE = Path(__file__).resolve().parents[1] / "native"
COMPILER = shutil.which("g++") or shutil.which("clang++")

@unittest.skipUnless(sys.platform.startswith("linux") and COMPILER, "Linux C++ host fixture required")
class BatteryPolicyNativeTests(unittest.TestCase):
    def test_graphics_ownership(self):
        with tempfile.TemporaryDirectory() as folder:
            exe = Path(folder) / "fixture"
            built = subprocess.run([COMPILER, "-std=c++17", "-O2", str(NATIVE / "battery_policy_test.cpp"), "-o", str(exe)],
                                   capture_output=True, text=True, timeout=60)
            self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
            run = subprocess.run([str(exe)], capture_output=True, text=True, timeout=30)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn("PASS battery ownership:", run.stdout)

if __name__ == "__main__":
    unittest.main()
