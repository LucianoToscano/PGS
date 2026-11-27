"""Rebrand only the verified PGS Java controls in a complete, already signed APK.

The input is the known-good PGS v0.3.8-pgs.3 full APK, NOT an unverified
Pokémon GO download. Native binaries, game DEX and resources must remain
byte-for-byte identical when decompressed. Android package/certificate remain
unchanged; only the PGS controls DEX, the PGS version in mode.json, and the
manifest versionCode may change. Device acceptance still requires testing.
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
import tempfile
import zipfile

import axml
import build
import nonroot
import pgs_update

SOURCE_SHA256 = "1e42c50f84afe5edf9570dfa808ba5e4be99b64d3ae28199b7316981c7414d4c"
SOURCE_VERSION_CODE = 2026111603
TARGET_VERSION_CODE = 2026111604
GAME_VERSION_NAME = "0.439.0"
PGS_VERSION = "v0.0.1"
TARGET_NAME = "PGS v0.0.1.apk"
MODE = "assets/pgrazor/mode.json"
MARKER = b"Ldev/pgrazor/Control;"
UPDATER = b"Ldev/pgrazor/Updater;"


def digest(path: Path) -> str:
    with Path(path).open("rb") as reader:
        return hashlib.file_digest(reader, "sha256").hexdigest()


def stream_digest(stream) -> str:
    hashed = hashlib.sha256()
    while data := stream.read(1024 * 1024):
        hashed.update(data)
    return hashed.hexdigest()


def module_dex_entry(archive: zipfile.ZipFile) -> str:
    matches = []
    for name in archive.namelist():
        if re.fullmatch(r"classes[0-9]*\.dex", name):
            with archive.open(name) as src:
                # The PGS control DEX is small, unlike the game's primary DEX files.
                if src.read(12_000_000).find(MARKER) >= 0:
                    matches.append(name)
    if len(matches) != 1:
        raise ValueError("Exactly one existing PGS controls DEX must be identified")
    with archive.open(matches[0]) as src:
        if UPDATER not in src.read():
            raise ValueError("Existing PGS DEX has no in-app updater")
    return matches[0]


def updated_mode(old: bytes) -> bytes:
    mode = json.loads(old)
    before = mode.get("pgrazorVersion")
    if not (isinstance(before, str) and before.startswith("v0.3.8-pgs.")
            and mode.get("compiledGameplay") is True):
        raise ValueError("Source APK is not the expected compiled PGS candidate")
    mode["pgrazorVersion"] = PGS_VERSION
    return json.dumps(mode, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def candidate(source: Path, controls: Path, output: Path) -> dict:
    source, controls, output = source.resolve(), controls.resolve(), output.resolve()
    if source == output or not source.is_file() or not controls.is_file():
        raise ValueError("Existing source APK, new controls DEX and distinct output required")
    if digest(source) != SOURCE_SHA256:
        raise ValueError("Source APK SHA-256 does not match the signed PGS v0.3.8-pgs.3")
    if pgs_update.cert_digests(source) != [pgs_update.PGS_SIGNER]:
        raise ValueError("Source APK has a foreign signing certificate")
    if not os.environ.get("PGRAZOR_KEYSTORE"):
        raise ValueError("Existing PGS signing keystore is mandatory")
    new_dex = controls.read_bytes()
    if (len(new_dex) < 200_000 or not new_dex.startswith(b"dex\n")
            or MARKER not in new_dex or UPDATER not in new_dex
            or PGS_VERSION.encode() not in new_dex):
        raise ValueError("Fresh controls DEX lacks PGS v0.0.1 classes or metadata")

    with zipfile.ZipFile(source) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or archive.testzip() is not None:
            raise ValueError("Invalid or duplicate entries in source PGS APK")
        dex_name = module_dex_entry(archive)
        if MODE not in names or "AndroidManifest.xml" not in names:
            raise ValueError("PGS manifest or control-mode asset missing")
        manifest = archive.read("AndroidManifest.xml")
        before = axml.inspect_manifest(manifest)
        if (before["package"] != pgs_update.GAME_PACKAGE
                or before["split"] is not None
                or before["versionCode"] != SOURCE_VERSION_CODE
                or before["versionName"] != GAME_VERSION_NAME
                or "lib/arm64-v8a/libil2cpp.so" not in names):
            raise ValueError("Unexpected PGS package, game runtime or source version")
        mode = updated_mode(archive.read(MODE))
        manifest = pgs_update.patch_manifest_version_code(
            manifest, SOURCE_VERSION_CODE, TARGET_VERSION_CODE)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="pgs-rebrand-") as root:
        unsigned = Path(root) / "unsigned.apk"
        aligned = Path(root) / "aligned.apk"
        with zipfile.ZipFile(source) as old, zipfile.ZipFile(unsigned, "w") as new:
            for entry in old.infolist():
                name = entry.filename
                if nonroot.signature_entry(name):
                    continue
                if name == dex_name:
                    new.writestr(copy.copy(entry), new_dex)
                elif name == MODE:
                    new.writestr(copy.copy(entry), mode)
                elif name == "AndroidManifest.xml":
                    new.writestr(copy.copy(entry), manifest)
                elif entry.is_dir():
                    new.writestr(copy.copy(entry), b"")
                else:
                    with old.open(entry) as reader, new.open(copy.copy(entry), "w") as writer:
                        shutil.copyfileobj(reader, writer, length=1024 * 1024)
        nonroot.command(build.android_tool("zipalign"), "-f", "-P", "16", "4", unsigned, aligned)
        nonroot.command(build.android_tool("apksigner"), "sign",
                        *build.signing_args(), "--out", output, aligned)
        if pgs_update.cert_digests(output) != [pgs_update.PGS_SIGNER]:
            output.unlink(missing_ok=True)
            raise RuntimeError("PGS signing certificate changed")
        nonroot.command(build.android_tool("zipalign"), "-c", "-P", "16", "4", output)

    with zipfile.ZipFile(source) as old, zipfile.ZipFile(output) as new:
        after = axml.inspect_manifest(new.read("AndroidManifest.xml"))
        old_names = {n for n in old.namelist() if not nonroot.signature_entry(n)}
        new_names = {n for n in new.namelist() if not nonroot.signature_entry(n)}
        if (new.testzip() is not None or new_names != old_names
                or after["package"] != before["package"]
                or after["versionCode"] != TARGET_VERSION_CODE
                or after["versionName"] != GAME_VERSION_NAME):
            output.unlink(missing_ok=True)
            raise RuntimeError("Repacked APK identity or archive integrity changed")
        assert json.loads(new.read(MODE))["pgrazorVersion"] == PGS_VERSION
        assert new.read(dex_name) == new_dex
        # A whole-archive digest comparison guarantees the original game, assets
        # and compiled native libraries were NOT changed by this targeted update.
        for name in sorted(old_names - {MODE, dex_name, "AndroidManifest.xml"}):
            with old.open(name) as a, new.open(name) as b:
                if stream_digest(a) != stream_digest(b):
                    output.unlink(missing_ok=True)
                    raise RuntimeError("Unexpected change to original APK member: " + name)
    if output.stat().st_size <= 100_000_000:
        output.unlink(missing_ok=True)
        raise RuntimeError("Refusing incomplete game package")
    return {
        "status": "SIGNED_COMPLETE_APK_VERIFIED",
        "apk": output.name, "bytes": output.stat().st_size,
        "sha256": digest(output), "source_apk_sha256": SOURCE_SHA256,
        "source_controls_dex": dex_name, "controls_dex_sha256": digest(controls),
        "pgs_version": PGS_VERSION, "game_version": GAME_VERSION_NAME,
        "package": pgs_update.GAME_PACKAGE, "installed_name": "Pokémon GO",
        "previous_version_code": SOURCE_VERSION_CODE,
        "version_code": TARGET_VERSION_CODE,
        "signing_certificate_sha256": pgs_update.PGS_SIGNER,
        "source_commit": os.environ.get("GITHUB_SHA"),
        "device_tested": False, "in_place_update_tested": False
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--controls", type=Path, default=build.BUILD / "pgrazor.dex")
    parser.add_argument("--output", type=Path, default=Path("dist/PGS") / TARGET_NAME)
    args = parser.parse_args()
    report = candidate(args.source, args.controls, args.output)
    (args.output.parent / "PGS.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output.parent / "SHA256SUMS.txt").write_text(
        report["sha256"] + "  " + args.output.name + "\n", encoding="utf-8")
    print("PGS v0.0.1 full APK signed, original game and native bytes preserved.")
    print("APK SHA-256:", report["sha256"])
    print("Android versionCode:", report["version_code"])
    print("Device install and login NOT tested.")


if __name__ == "__main__":
    main()
