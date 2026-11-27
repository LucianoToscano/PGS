"""Verify retired source names and the original LP64 type/value contract."""
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
    def test_all_native_names_use_pgs_no_legacy(self):
        inventory = aliases()
        self.assertGreaterEqual(len(inventory), 113)
        # No retired pgrazor names should remain anywhere in native sources.
        for path in NATIVE.rglob("*"):
            if not path.is_file() or path.suffix not in {".h", ".hpp", ".cpp", ".c", ".cc", ".inc"}:
                continue
            if path.name == "pvp_icons.h":
                continue
            data = path.read_bytes()
            self.assertNotRegex(data, rb"(?i)pgrazor", str(path.relative_to(ROOT)))
        # Every inventory entry uses pgs_ naming (no pgrazor legacy aliases).
        for entry in inventory:
            old, new = entry["old"], entry["new"]
            with self.subTest(alias=new):
                self.assertNotRegex(old, r"(?i)pgrazor", f"legacy old name: {old}")
                self.assertNotRegex(new, r"(?i)pgrazor", f"legacy new name: {new}")
                self.assertTrue(entry["retired"])
                path = ROOT / entry["header"]
                self.assertTrue(path.resolve().is_relative_to(NATIVE.resolve()))
                source = path.read_text(encoding="utf-8", errors="surrogateescape")
                self.assertRegex(source, r"\b" + re.escape(new) + r"\b")
                self.assertTrue(entry["abi_before"])

    @unittest.skipUnless(sys.platform.startswith("linux") and COMPILER,
                         "Native ABI baseline compilation requires Linux C++17")
    def test_canonical_types_and_constants_keep_original_abi(self):
        by_header = defaultdict(list)
        for entry in aliases():
            by_header[entry["header"]].append(entry)
        for header, entries in sorted(by_header.items()):
            with self.subTest(header=header):
                code = ['#include <type_traits>', '#include "' + Path(header).name + '"']
                for entry in entries:
                    name, facts = entry["new"], entry["abi_before"]
                    if entry["kind"] == "type":
                        code.extend([f"static_assert(sizeof({name}) == {facts['size']});",
                                     f"static_assert(alignof({name}) == {facts['align']});"])
                    else:
                        value = facts["value"]
                        self.assertRegex(value, r"^-?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?$")
                        code.append(f"static_assert(static_cast<long double>({name}) == static_cast<long double>({value}L));")
                        if entry["kind"] == "enumerator":
                            code.append(f"static_assert(std::is_enum_v<decltype({name})>);")
                run = subprocess.run([COMPILER, "-std=c++17", "-fsyntax-only", "-x", "c++",
                                      "-I", str(NATIVE), "-"], input="\n".join(code)+"\n",
                                     text=True, capture_output=True, timeout=60)
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    @unittest.skipUnless(sys.platform.startswith("linux") and COMPILER,
                         "Native getter declarations require Linux C++17")
    def test_private_canonical_getter_declarations_link(self):
        names = ("runtime_metadata", "runtime_bootstrap", "runtime_transport",
                 "unity_scheduler", "shared_host", "accounts", "adventure_sync", "account_host")
        code = ['#include <type_traits>']
        code.extend('#include "'+name+'.h"' for name in names)
        assertions = []
        for name in names:
            new = "pgs_"+name+"_api"
            typ = "pgs_accounts_api_v1_t" if name == "accounts" else "unsigned"
            ret = "const pgs_accounts_api_v1_t*" if name == "accounts" else "const void*"
            code.append(f'extern "C" {ret} {new}(uint32_t version) {{ static {typ} value{{}}; return version == 1 ? &value : nullptr; }}')
            code.append(f"static_assert(std::is_same_v<decltype(&{new}), {ret}(*)(uint32_t)>);")
            assertions.append(f"if (!{new}(1) || {new}(0) || {new}(2)) return 1;")
        code.extend(["int main(){", *assertions, "return 0; }"])
        with tempfile.TemporaryDirectory(prefix="pgs-getters-") as work:
            exe = Path(work)/"getters"
            built = subprocess.run([COMPILER,"-std=c++17","-x","c++","-I",str(NATIVE),"-","-o",str(exe)],
                                   input="\n".join(code)+"\n",text=True,capture_output=True,timeout=60)
            self.assertEqual(built.returncode,0,built.stdout+built.stderr)
            run = subprocess.run([str(exe)],capture_output=True,text=True,timeout=10)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)

    def test_private_native_legacy_names_do_not_return(self):
        for path in NATIVE.rglob("*"):
            if not path.is_file() or path.suffix not in {".h",".hpp",".cpp",".c",".cc",".inc"}:
                continue
            data = path.read_bytes()
            # Only the public factory spelling and the icon-source notice are retained.
            if path.name == "pvp_icons.h":
                continue
            data = data.replace(b"pgrazor_native_api",b"")
            self.assertNotRegex(data,rb"(?i)pgrazor",str(path.relative_to(ROOT)))


if __name__ == "__main__":
    unittest.main()
