"""Run the real buddy-feeding state machine without a game or Android device.

The fixture replaces hook installation and time only. Managed calls and roots
remain simulated by buddy_feeding_test.cpp, as in its Android core harness.
This does not validate Dobby trampolines or live game metadata.
"""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


NATIVE = Path(__file__).resolve().parents[1] / 'native'


@unittest.skipUnless(sys.platform.startswith('linux'), 'Linux host fixture required')
class BuddyFeedingNativeTests(unittest.TestCase):
    def test_pending_recovery_and_native_lifetime_scenarios(self):
        compiler = shutil.which('c++') or shutil.which('g++') or shutil.which('clang++')
        if not compiler:
            self.skipTest('C++17 host compiler unavailable')
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            # hook_engine.h needs only this type here: the fixture supplies the
            # hook bridge, and no Dobby implementation is linked or exercised.
            (work / 'dobby.h').write_text(
                '#pragma once\n'
                'typedef void (*dobby_instrument_callback_t)(void *, void *);\n',
                encoding='utf-8')
            executable = work / 'buddy-feeding-test'
            built = subprocess.run([
                compiler, '-std=c++17', '-O2', '-pthread',
                '-DPGS_BUDDY_HOST_TEST', '-I' + str(work),
                str(NATIVE / 'buddy_feeding.cpp'),
                str(NATIVE / 'buddy_feeding_test.cpp'),
                '-Wl,--wrap=clock_gettime,--wrap=nanosleep', '-ldl',
                '-o', str(executable),
            ], text=True, capture_output=True, timeout=60)
            self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
            result = subprocess.run([str(executable)], text=True,
                                    capture_output=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('PASS native buddy feeding:', result.stdout)
            self.assertIn('same-buddy fed observation', result.stdout)


if __name__ == '__main__':
    unittest.main()
