"""Create a PGS update retaining the original Pokémon GO Android identity.

Use the existing PGS signing key: never generate a new key and never rename
the package. Only increase the manifest versionCode; preserve game resources,
native code, class names, application label and versionName. A fresh Android
installation and in-place update still require a device test.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import tempfile
import zipfile

import axml
import build
import nonroot

GAME_PACKAGE = "com.nianticlabs.pokemongo"
PGS_SIGNER = "d95c6bdfcbd91dc5c9cde698487c88e4994771a475e4efde4567b8d5f44e96cf"
MAX_VERSION_CODE = 2_100_000_000


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def next_version_code(game_version_code: int, previous_pgs_version_code: int) -> int:
    """Keep versionCode increasing even for another PGS build of the same game."""
    if (type(game_version_code) is not int
            or type(previous_pgs_version_code) is not int
            or not (1 <= game_version_code < MAX_VERSION_CODE)
            or not (1 <= previous_pgs_version_code < MAX_VERSION_CODE)):
        raise ValueError("Android versionCode must be a positive supported integer")
    result = max(game_version_code, previous_pgs_version_code + 1)
    if result >= MAX_VERSION_CODE:
        raise ValueError("No remaining supported versionCode")
    return result


def patch_manifest_version_code(data: bytes, old_code: int, new_code: int,
                                package: str = GAME_PACKAGE) -> bytes:
    before = axml.inspect_manifest(data)
    if (before["package"] != package or before["split"] is not None
            or before["applications"] != 1 or before["versionCode"] != old_code):
        raise ValueError("Unexpected package, split, or versionCode")
    if not old_code < new_code < MAX_VERSION_CODE:
        raise ValueError("New versionCode must be higher")
    header, chunks, pool, _, _ = axml._parse(data)
    edited = 0
    output = []
    for kind, source in chunks:
        if kind == 0x102:
            raw = bytearray(source)
            h = axml._u16(raw, 2)
            tag = pool.string(axml._u32(raw, h + 4))
            if tag == "manifest":
                start, size, count = struct.unpack_from("<HHH", raw, h + 8)
                for index in range(count):
                    at = h + start + index * size
                    ns = pool.string(axml._u32(raw, at))
                    key = pool.string(axml._u32(raw, at + 4))
                    if ns == axml.ANDROID_NS and key == "versionCode":
                        # Android's typed integer is at +16; keep every other
                        # manifest chunk and byte untouched.
                        if raw[at + 15] not in (0x10, 0x11):
                            raise ValueError("Expected typed integer versionCode")
                        if axml._u32(raw, at + 16) != old_code:
                            raise ValueError("VersionCode's raw bytes do not match")
                        struct.pack_into("<I", raw, at + 16, new_code)
                        edited += 1
            source = bytes(raw)
        output.append((kind, source))
    if edited != 1:
        raise ValueError("Expected exactly one versionCode attribute")
    body = b"".join(chunk for _, chunk in output)
    prefix = bytearray(data[:header])
    struct.pack_into("<I", prefix, 4, header + len(body))
    result = bytes(prefix) + body
    after = axml.inspect_manifest(result)
    if (after["versionCode"] != new_code or after["package"] != package
            or after["versionName"] != before["versionName"]
            or after["minSdkVersion"] != before["minSdkVersion"]
            or after["providers"] != before["providers"]
            or after["activities"] != before["activities"]):
        raise ValueError("Unexpected change to Android identity or components")
    return result


def cert_digests(apk: Path) -> list[str]:
    verification = nonroot.command(
        build.android_tool("apksigner"), "verify", "--print-certs",
        apk, capture=True)
    return [v.lower() for v in re.findall(
        r"Signer #\d+ certificate SHA-256 digest: ([0-9a-fA-F]+)",
        verification.stdout)]


def create_update(source: Path, destination: Path,
                  expected_sha256: str, previous_version_code: int) -> dict:
    source, destination = source.resolve(), destination.resolve()
    if source == destination or not source.is_file():
        raise ValueError("Input APK must exist and must not be overwritten")
    if (not re.fullmatch(r"[0-9a-f]{64}", expected_sha256)
            or sha256(source) != expected_sha256):
        raise ValueError("APK input SHA-256 differs from the verified PGS release")
    if cert_digests(source) != [PGS_SIGNER]:
        raise ValueError("The original PGS candidate uses a different certificate")
    if not os.environ.get("PGS_KEYSTORE"):
        raise ValueError("PGS release keystore is mandatory; no development key allowed")
    with zipfile.ZipFile(source) as apk:
        original_names = apk.namelist()
        if len(original_names) != len(set(original_names)) or apk.testzip() is not None:
            raise ValueError("Corrupt or duplicate APK entries")
        before = axml.inspect_manifest(apk.read("AndroidManifest.xml"))
        if before["package"] != GAME_PACKAGE or before["split"] is not None:
            raise ValueError("PGS update must keep the original Pokémon GO package")
        old_code = before["versionCode"]
        new_code = next_version_code(old_code, previous_version_code)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="pgs-update-") as working:
        unsigned = Path(working) / "unsigned.apk"
        aligned = Path(working) / "aligned.apk"
        with zipfile.ZipFile(source) as original, zipfile.ZipFile(unsigned, "w") as result:
            for entry in original.infolist():
                if nonroot.signature_entry(entry.filename):
                    continue
                if entry.filename == "AndroidManifest.xml":
                    result.writestr(
                        copy.copy(entry),
                        patch_manifest_version_code(original.read(entry),
                                                    old_code, new_code))
                elif entry.is_dir():
                    result.writestr(copy.copy(entry), b"")
                else:
                    with original.open(entry) as reader, result.open(copy.copy(entry), "w") as writer:
                        shutil.copyfileobj(reader, writer, length=1024 * 1024)
        nonroot.command(build.android_tool("zipalign"), "-f", "-P", "16",
                        "4", unsigned, aligned)
        nonroot.command(build.android_tool("apksigner"), "sign",
                        *build.signing_args(), "--out", destination, aligned)
        if cert_digests(destination) != [PGS_SIGNER]:
            destination.unlink(missing_ok=True)
            raise RuntimeError("Signer certificate changed; update cannot be published")
        nonroot.command(build.android_tool("zipalign"), "-c", "-P", "16",
                        "4", destination)
    with zipfile.ZipFile(destination) as final:
        after = axml.inspect_manifest(final.read("AndroidManifest.xml"))
        if (final.testzip() is not None or after["package"] != GAME_PACKAGE
                or after["versionCode"] != new_code
                or after["versionName"] != before["versionName"]):
            destination.unlink(missing_ok=True)
            raise RuntimeError("PGS candidate package integrity check failed")
    return {"status": "SIGNED_PACKAGE_VERIFIED", "apk": destination.name,
            "sha256": sha256(destination), "bytes": destination.stat().st_size,
            "package": GAME_PACKAGE, "game_version_name": before["versionName"],
            "previous_version_code": previous_version_code,
            "source_version_code": old_code, "version_code": new_code,
            "signing_certificate_sha256": PGS_SIGNER, "device_tested": False,
            "source_apk_sha256": expected_sha256}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--previous-version-code", required=True, type=int)
    args = parser.parse_args()
    report = create_update(args.input, args.output,
                           args.expected_sha256, args.previous_version_code)
    args.output.with_suffix(".json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    print("Signed PGS APK created; package retained:", report["package"])
    print("VersionCode:", report["source_version_code"], "->", report["version_code"])
    print("SHA-256:", report["sha256"])
    print("Install and login have not been tested on a phone.")


if __name__ == "__main__":
    main()
