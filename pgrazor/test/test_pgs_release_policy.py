"""Verify future full PGS releases inherit the monotonic Android code policy."""
import sys
import struct
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import axml
import release_apk
from test_axml import chunk
from test_pgs_update import manifest_with_version


def game_manifest():
    fixture = manifest_with_version()
    _, chunks, pool, _, _ = axml._parse(fixture)
    replacement = pool.add("com.nianticlabs.pokemongo")
    new_nodes = []
    for kind, data in chunks[1:]:
        if kind == 0x102:
            raw = bytearray(data)
            h = axml._u16(raw, 2)
            if pool.string(axml._u32(raw, h + 4)) == "manifest":
                start, size, count = struct.unpack_from("<HHH", raw, h + 8)
                for i in range(count):
                    at = h + start + i * size
                    if pool.string(axml._u32(raw, at + 4)) == "package":
                        struct.pack_into("<I", raw, at + 8, replacement)
                        struct.pack_into("<I", raw, at + 16, replacement)
                data = bytes(raw)
        new_nodes.append(data)
    return chunk(3, pool.build() + b"".join(new_nodes))


class PgsReleasePolicyTests(unittest.TestCase):
    def test_repacked_release_keeps_package_and_bumps_android_code(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d) / "base.apk"
            split = Path(d) / "split.apk"
            out = Path(d) / "release.apk"
            with zipfile.ZipFile(base, "w") as data:
                data.writestr("AndroidManifest.xml", game_manifest())
                data.writestr("classes.dex", b"original dex fixture")
            with zipfile.ZipFile(split, "w") as data:
                data.writestr("lib/arm64-v8a/libil2cpp.so", b"original native fixture")
                data.writestr("AndroidManifest.xml", b"split fixture")
            rows = [(base, {"split": None}), (split, {"split": "config.arm64_v8a"})]
            with patch.object(release_apk.nonroot, "inspect_set", return_value=(
                    "com.nianticlabs.pokemongo", base, rows, {"arm64-v8a"})):
                release_apk.merge([base, split], out, pgs_previous_version_code=2026111603)
                with zipfile.ZipFile(out) as result:
                    info = axml.inspect_manifest(result.read("AndroidManifest.xml"))
                    self.assertEqual(info["package"], "com.nianticlabs.pokemongo")
                    self.assertEqual(info["versionCode"], 2026111604)
                    self.assertEqual(result.read("classes.dex"), b"original dex fixture")
                    self.assertEqual(result.read("lib/arm64-v8a/libil2cpp.so"),
                                     b"original native fixture")
                release_apk.merge([base, split], out)
                with zipfile.ZipFile(out) as result:
                    original = axml.inspect_manifest(result.read("AndroidManifest.xml"))
                    self.assertEqual(original["versionCode"], 2026111602)


if __name__ == "__main__":
    unittest.main()
