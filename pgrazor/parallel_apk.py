"""Build an experimental independently installable PGS package from a signed game build.

This only changes Android's *external* application identity. It does NOT assert that
Niantic sign-in, Play Integrity, device checks or gameplay support a renamed app.
The original PGS.apk is never altered. Run on the trusted build runner so the same
PGS release certificate signs the resulting APK.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import struct
import tempfile
import zipfile

import axml
import build
import nonroot

ORIGINAL_PACKAGE = "com.nianticlabs.pokemongo"
PGS_PACKAGE = "app.pgs.spoofers"
PGS_LABEL = "PGS"
PGS_CERT_SHA256 = "d95c6bdfcbd91dc5c9cde698487c88e4994771a475e4efde4567b8d5f44e96cf"
SOURCE_APK_SHA256 = "595103b36163776b919befe57ae399b2dcc1dff0234e2c0686331389926d137b"
COMPONENTS = {
    "application", "activity", "activity-alias", "service", "receiver",
    "provider", "instrumentation",
}
CLASS_ATTRS = {"name", "targetActivity", "backupAgent", "appComponentFactory",
               "manageSpaceActivity"}
PACKAGE_PERMISSION_TAGS = {"permission", "permission-group", "permission-tree",
                           "uses-permission", "uses-permission-sdk-23",
                           "uses-permission-sdk-m"}


def sha256(path: Path) -> str:
    with path.open("rb") as data:
        return hashlib.file_digest(data, "sha256").hexdigest()


def rewrite_package_name(text: str) -> str:
    """Change only app-owned authorities and names, never arbitrary text."""
    if text == ORIGINAL_PACKAGE or text.startswith(ORIGINAL_PACKAGE + "."):
        return PGS_PACKAGE + text[len(ORIGINAL_PACKAGE):]
    return text


def patch_manifest(data: bytes) -> bytes:
    """Rewrite the manifest package, launcher label and app-owned authorities.

    Relative component class names must become absolute before changing the
    manifest's package. Otherwise Android would load them from app.pgs.spoofers
    instead of their existing original Java namespaces.
    """
    before = axml.inspect_manifest(data)
    if (before["package"] != ORIGINAL_PACKAGE or before["split"] is not None
            or before["applications"] != 1):
        raise ValueError("Expected the validated standalone original-game manifest")

    header, chunks, pool, _, _ = axml._parse(data)
    out = []
    edits = {"package": 0, "label": 0, "provider": 0}

    def typed_string(attr: bytearray, at: int):
        if attr[at + 15] != 3:
            return None
        return pool.string(axml._u32(attr, at + 16))

    def set_string(attr: bytearray, at: int, value: str):
        index = pool.add(value)
        struct.pack_into("<I", attr, at + 8, index)
        struct.pack_into("<HBBI", attr, at + 12, 8, 0, 3, index)

    for kind, original in chunks:
        if kind != 0x102:
            out.append((kind, original))
            continue
        raw = bytearray(original)
        h = axml._u16(raw, 2)
        tag = pool.string(axml._u32(raw, h + 4))
        start, size, count = struct.unpack_from("<HHH", raw, h + 8)
        if size < 20:
            raise ValueError("Malformed Android XML attribute size")

        unity_activity = False
        if tag == "activity":
            for i in range(count):
                at = h + start + i * size
                if (pool.string(axml._u32(raw, at + 4)) == "name"
                        and typed_string(raw, at)
                        == "com.nianticproject.holoholo.libholoholo.unity.UnityMainActivity"):
                    unity_activity = True

        for i in range(count):
            at = h + start + i * size
            ns = pool.string(axml._u32(raw, at))
            key = pool.string(axml._u32(raw, at + 4))
            value = typed_string(raw, at)
            if (tag == "manifest" and ns is None and key == "package"):
                if value != ORIGINAL_PACKAGE:
                    raise ValueError("Unexpected input manifest package")
                set_string(raw, at, PGS_PACKAGE)
                edits["package"] += 1
            elif (tag == "manifest" and ns == axml.ANDROID_NS and key == "sharedUserId"):
                raise ValueError("Shared-user manifests must not be cloned")
            elif ns == axml.ANDROID_NS and key == "label" and (
                    tag == "application" or unity_activity):
                set_string(raw, at, PGS_LABEL)
                edits["label"] += 1
            elif ns == axml.ANDROID_NS and key == "authorities" and tag == "provider":
                if not isinstance(value, str):
                    raise ValueError("Cannot safely rewrite resource-backed provider authority")
                changed = ";".join(rewrite_package_name(part) for part in value.split(";"))
                if changed != value:
                    set_string(raw, at, changed)
                    edits["provider"] += 1
            elif (ns == axml.ANDROID_NS and key in CLASS_ATTRS and tag in COMPONENTS
                  and isinstance(value, str) and not value.startswith("android.")):
                # Class names are *not* package-renamed. Relative declarations
                # must resolve to the original class namespace after the move.
                if key in CLASS_ATTRS and value.startswith("."):
                    set_string(raw, at, ORIGINAL_PACKAGE + value)
                elif key in CLASS_ATTRS and "." not in value:
                    set_string(raw, at, ORIGINAL_PACKAGE + "." + value)
            elif ns == axml.ANDROID_NS and key == "permission" and tag in COMPONENTS:
                if isinstance(value, str):
                    updated = rewrite_package_name(value)
                    if updated != value:
                        set_string(raw, at, updated)
            elif (ns == axml.ANDROID_NS and key == "name"
                  and tag in PACKAGE_PERMISSION_TAGS):
                if isinstance(value, str):
                    updated = rewrite_package_name(value)
                    if updated != value:
                        set_string(raw, at, updated)
            elif ns == axml.ANDROID_NS and key == "taskAffinity":
                if isinstance(value, str):
                    updated = rewrite_package_name(value)
                    if updated != value:
                        set_string(raw, at, updated)

        out.append((kind, bytes(raw)))

    out[0] = (1, pool.build())
    body = b"".join(block for _, block in out)
    header_bytes = bytearray(data[:header])
    struct.pack_into("<I", header_bytes, 4, header + len(body))
    result = bytes(header_bytes) + body

    after = axml.inspect_manifest(result)
    if (after["package"] != PGS_PACKAGE or after["split"] is not None
            or after["applications"] != 1
            or after["versionCode"] != before["versionCode"]
            or after["versionName"] != before["versionName"]):
        raise ValueError("Cloned manifest identity/version verification failed")
    if edits["package"] != 1 or edits["label"] < 1:
        raise ValueError("Required package or application label not rewritten")
    if any(rewrite_package_name(str(p["authorities"])) != str(p["authorities"])
           for p in after["providers"]):
        raise ValueError("An original app-owned provider authority was retained")
    return result


def build_parallel(source: Path, output: Path) -> dict:
    if not source.is_file() or source.resolve() == output.resolve():
        raise ValueError("Source must exist and must not be overwritten")
    digest = sha256(source)
    if digest != SOURCE_APK_SHA256:
        raise ValueError("Source APK differs from previously verified PGS release")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="pgs-parallel-") as temporary:
        tmp = Path(temporary)
        unsigned = tmp / "unsigned.apk"
        aligned = tmp / "aligned.apk"
        with zipfile.ZipFile(source) as archive, zipfile.ZipFile(unsigned, "w") as dest:
            if archive.testzip() is not None:
                raise ValueError("Source ZIP has a checksum error")
            if len(archive.namelist()) != len(set(archive.namelist())):
                raise ValueError("Duplicate archive entry")
            names = set()
            for entry in archive.infolist():
                name = entry.filename
                if nonroot.signature_entry(name):
                    continue  # v1 signatures are invalidated by any manifest edit
                names.add(name)
                if name == "AndroidManifest.xml":
                    patched = patch_manifest(archive.read(entry))
                    dest.writestr(copy.copy(entry), patched)
                elif entry.is_dir():
                    dest.writestr(copy.copy(entry), b"")
                else:
                    with archive.open(entry) as reader, dest.open(copy.copy(entry), "w") as writer:
                        import shutil
                        shutil.copyfileobj(reader, writer, length=1024 * 1024)
            if "AndroidManifest.xml" not in names or "lib/arm64-v8a/libil2cpp.so" not in names:
                raise ValueError("Required manifest or ARM64 game payload missing")
        nonroot.command(build.android_tool("zipalign"), "-f", "-P", "16",
                        "4", unsigned, aligned)
        nonroot.command(build.android_tool("apksigner"), "sign", *build.signing_args(),
                        "--out", output, aligned)
        verification = nonroot.command(build.android_tool("apksigner"), "verify",
                                       "--print-certs", output, capture=True)
        match = re.findall(r"Signer #\d+ certificate SHA-256 digest: ([0-9a-fA-F]+)",
                           verification.stdout)
        if [m.lower() for m in match] != [PGS_CERT_SHA256]:
            output.unlink(missing_ok=True)
            raise RuntimeError("PGS release signing identity changed")
        nonroot.command(build.android_tool("zipalign"), "-c", "-P", "16", "4", output)
    with zipfile.ZipFile(output) as archive:
        manifest = axml.inspect_manifest(archive.read("AndroidManifest.xml"))
        if manifest["package"] != PGS_PACKAGE or archive.testzip() is not None:
            output.unlink(missing_ok=True)
            raise RuntimeError("Packaged clone manifest or ZIP validation failed")
    return {"status": "PACKAGE_ONLY_VERIFIED", "apk": output.name,
            "bytes": output.stat().st_size, "sha256": sha256(output),
            "package": PGS_PACKAGE, "label": PGS_LABEL,
            "source_sha256": digest, "certificate_sha256": PGS_CERT_SHA256,
            "device_tested": False,
            "limitations": ["Play Integrity, Google/Niantic login and gameplay NOT tested",
                            "Changing package ID may break game or external integrations",
                            "Original game and prior PGS.apk preserved"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = build_parallel(args.input, args.output)
    result_path = args.output.with_suffix(".json")
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print("Signed PGS parallel candidate:", args.output)
    print("Manifest package:", result["package"])
    print("SHA-256:", result["sha256"])
    print("Not device-tested.")


if __name__ == "__main__":
    main()
