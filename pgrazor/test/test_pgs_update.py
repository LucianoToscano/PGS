"""Protect Android package identity and monotonically increasing PGS version codes."""
import sys
from pathlib import Path
import struct
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import axml
import pgs_update
from test_axml import chunk, fixture


def manifest_with_version(code=2026111602):
    base = fixture()
    _, chunks, pool, _, _ = axml._parse(base)
    ns = pool.add(axml.ANDROID_NS)
    key = pool.add("versionCode")
    attr = struct.pack("<IIIHBBI", ns, key, axml.NO_INDEX, 8, 0, 0x10, code)
    result = []
    inserted = False
    for kind, data in chunks[1:]:
        if kind == 0x102 and not inserted:
            raw = bytearray(data)
            # Original fixture manifest has one package attribute.
            count = axml._u16(raw, 28)
            struct.pack_into("<H", raw, 28, count + 1)
            raw.extend(attr)
            struct.pack_into("<I", raw, 4, len(raw))
            data = bytes(raw)
            inserted = True
        result.append(data)
    if not inserted:
        raise AssertionError("Fixture did not contain a manifest")
    return chunk(3, pool.build() + b"".join(result))


class PgsUpdateTests(unittest.TestCase):
    def test_monotonic_version_code_same_game(self):
        self.assertEqual(pgs_update.next_version_code(2026111602, 2026111602),
                         2026111603)

    def test_monotonic_version_code_newer_game(self):
        self.assertEqual(pgs_update.next_version_code(2027010103, 2026111603),
                         2027010103)

    def test_monotonic_version_code_older_game(self):
        self.assertEqual(pgs_update.next_version_code(2026111602, 2026111604),
                         2026111605)

    def test_in_range_and_no_overflow(self):
        for a, b in [(0, 1), (1, 0), (2026111602, 2100000000),
                     (-1, 20), (True, 20)]:
            with self.subTest((a, b)), self.assertRaises(ValueError):
                pgs_update.next_version_code(a, b)

    def test_manifest_patch_changes_only_version_code(self):
        before = manifest_with_version()
        old = axml.inspect_manifest(before)
        self.assertEqual(old["versionCode"], 2026111602)
        modified = pgs_update.patch_manifest_version_code(
            before, 2026111602, 2026111603, package="dev.example.test")
        new = axml.inspect_manifest(modified)
        self.assertEqual(new["versionCode"], 2026111603)
        for key in ["package", "versionName", "minSdkVersion", "activities",
                    "providers", "split"]:
            self.assertEqual(old[key], new[key])
        self.assertEqual(len(before), len(modified))
        _, old_chunks, _, _, _ = axml._parse(before)
        _, new_chunks, _, _, _ = axml._parse(modified)
        differences = [i for i, (a, b) in enumerate(zip(old_chunks, new_chunks))
                       if a != b]
        self.assertEqual(differences, [1])

    def test_rejects_downgrade_and_wrong_identity(self):
        before = manifest_with_version()
        for old, new, package in [(2026111603, 2026111604, "dev.example.test"),
                                  (2026111602, 2026111602, "dev.example.test"),
                                  (2026111602, 2026111603, pgs_update.GAME_PACKAGE)]:
            with self.subTest((old, new, package)), self.assertRaises(ValueError):
                pgs_update.patch_manifest_version_code(before, old, new, package)


if __name__ == "__main__":
    unittest.main()
