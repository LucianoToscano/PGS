"""Verify PGS source aliases without altering the installed native ABI."""
from collections import defaultdict
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
NATIVE = ROOT / "pgs" / "native"
INVENTORY = ROOT / "docs" / "PGS_NATIVE_ALIAS_INVENTORY.json"
COMPILER = shutil.which("g++") or shutil.which("clang++")


def aliases():
    return json.loads(INVENTORY.read_text(encoding="utf-8"))


class PgsNativeAliasesTests(unittest.TestCase):
    def test_source_alias_contract(self):
        inventory = aliases()
        self.assertTrue(inventory)
        old_names, new_names = set(), set()
        for entry in inventory:
            old, new = entry["old"], entry["new"]
            with self.subTest(alias=new):
                self.assertNotIn(old, old_names)
                self.assertNotIn(new, new_names)
                old_names.add(old)
                new_names.add(new)
                self.assertGreater(entry["migrated_uses"], 0)
                path = ROOT / entry["header"]
                self.assertTrue(path.resolve().is_relative_to(NATIVE.resolve()))
                source = path.read_text(encoding="utf-8", errors="surrogateescape")
                if entry["kind"] == "constant":
                    self.assertTrue(old.startswith("PGRAZOR_"))
                    self.assertEqual(new, "PGS_" + old[8:])
                    pattern = r"(?m)^[ \t]*#[ \t]*define[ \t]+" + re.escape(old) + r"[ \t]+" + re.escape(new) + r"[ \t]*$"
                elif entry["kind"] == "enumerator":
                    self.assertTrue(old.startswith("PGRAZOR_"))
                    self.assertEqual(new, "PGS_" + old[8:])
                    pattern = r"\b" + re.escape(old) + r"\s*=\s*" + re.escape(new) + r"\s*,"
                    self.assertNotRegex(source, r"(?m)^\s*#\s*define\s+" + re.escape(old) + r"\b")
                else:
                    self.assertEqual(entry["kind"], "type")
                    self.assertTrue(old.startswith("pgrazor_"))
                    self.assertEqual(new, "pgs_" + old[8:])
                    pattern = r"\btypedef\s+" + re.escape(old) + r"\s+" + re.escape(new) + r"\s*;"
                self.assertRegex(source, pattern)

    @unittest.skipUnless(sys.platform.startswith("linux") and COMPILER,
                         "Native alias compilation requires a Linux C++17 compiler")
    def test_all_aliases_have_identical_type_or_constant_value(self):
        by_header = defaultdict(list)
        for entry in aliases():
            by_header[entry["header"]].append(entry)
        for header, entries in sorted(by_header.items()):
            with self.subTest(header=header):
                name = (ROOT / header).relative_to(NATIVE).as_posix()
                code = ['#include <type_traits>', '#include "' + name + '"']
                for entry in entries:
                    old, new = entry["old"], entry["new"]
                    if entry["kind"] == "type":
                        code.append("static_assert(std::is_same_v<" + old + ", " + new + ">);")
                    else:
                        code.append("static_assert((" + old + ") == (" + new + "));")
                        if entry["kind"] == "enumerator":
                            code.append("static_assert(std::is_same_v<decltype(" + old + "), decltype(" + new + ")>);")
                            code.extend(["#ifdef " + old, "#error legacy enumerator became a macro", "#endif"])
                result = subprocess.run(
                    [COMPILER, "-std=c++17", "-fsyntax-only", "-x", "c++",
                     "-I" + str(NATIVE), "-"],
                    input="\n".join(code) + "\n", text=True,
                    capture_output=True, timeout=60
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


    @unittest.skipUnless(sys.platform.startswith("linux") and COMPILER,
                         "Native getter forwarding requires a Linux C++17 compiler")
    def test_private_getters_forward_the_same_version_and_pointer(self):
        # Synthetic implementations verify source alias behavior without a game,
        # external native library, hooks, or a device.
        names = ("runtime_metadata", "runtime_bootstrap", "runtime_transport",
                 "unity_scheduler", "shared_host", "accounts",
                 "adventure_sync", "account_host")
        code = ['#include <type_traits>']
        code.extend('#include "' + name + '.h"' for name in names)
        assertions = []
        for name in names:
            old, new = "pgrazor_" + name + "_api", "pgs_" + name + "_api"
            typ = "pgs_accounts_api_v1_t" if name == "accounts" else "unsigned"
            ret = "const pgs_accounts_api_v1_t*" if name == "accounts" else "const void*"
            code.append('extern "C" ' + ret + ' ' + old +
                        '(uint32_t version) { static ' + typ +
                        ' value{}; return version == 1 ? &value : nullptr; }')
            code.append('static_assert(std::is_same_v<decltype(&' + old +
                        '), decltype(&' + new + ')>);')
            assertions.append('if (!' + new + '(1) || ' + new + '(1) != ' +
                              old + '(1) || ' + new + '(0) || ' +
                              new + '(2)) return 1;')
        code.extend(['int main() {', *assertions, 'return 0; }'])
        with tempfile.TemporaryDirectory(prefix="pgs-getter-aliases-") as work:
            executable = Path(work) / "forwarding"
            result = subprocess.run(
                [COMPILER, "-std=c++17", "-x", "c++", "-I", str(NATIVE),
                 "-", "-o", str(executable)],
                input="\n".join(code) + "\n", text=True,
                capture_output=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            run = subprocess.run([str(executable)], capture_output=True,
                                 text=True, timeout=10)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)


if __name__ == "__main__":
    unittest.main()
