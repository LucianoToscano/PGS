"""Read-only validation of a full PGS candidate. Never signs, installs or publishes an APK."""
from pathlib import Path
import argparse
import json
import re
import zipfile

import axml
import build
import nonroot
import pgs_update

MIN_APK_BYTES = 100_000_000
MAX_DEX_BYTES = 256 * 1024 * 1024
MACHINES = {"arm64-v8a": 183, "x86_64": 62}
REQUIRED_CLASSES = (
    b"Ldev/pgs/BootstrapProvider;", b"Ldev/pgs/Control;", b"Ldev/pgs/Updater;",
)
MODE = "assets/pgs/mode.json"


def read_bounded(archive, name, limit):
    info = archive.getinfo(name)
    if not 0 < info.file_size <= limit:
        raise ValueError("Unexpected entry size: " + name)
    return archive.read(info)


def verify_elf(archive, name, machine):
    with archive.open(name) as stream:
        header = stream.read(20)
    if (len(header) != 20 or header[:6] != b"\x7fELF\x02\x01"
            or int.from_bytes(header[18:20], "little") != machine):
        raise ValueError("Wrong 64-bit ELF architecture: " + name)


def verify(apk, *, tag, game_version, game_version_code, previous_version_code):
    """Check the new coordinated layout against explicitly expected release identity."""
    apk = Path(apk)
    if not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", tag):
        raise ValueError("Expected a stable PGS version tag")
    expected_code = pgs_update.next_version_code(game_version_code, previous_version_code)
    if not apk.is_file() or apk.stat().st_size <= MIN_APK_BYTES:
        raise ValueError("Incomplete APK: a controls preview is not a release")
    if pgs_update.cert_digests(apk) != [pgs_update.PGS_SIGNER]:
        raise ValueError("PGS signing certificate mismatch")
    nonroot.command(build.android_tool("zipalign"), "-c", "-P", "16", "4", apk)
    with zipfile.ZipFile(apk) as archive:
        names = archive.namelist()
        members = set(names)
        if len(names) != len(members) or archive.testzip() is not None:
            raise ValueError("Invalid ZIP or duplicate APK entries")
        required = {"AndroidManifest.xml", "classes.dex", "resources.arsc",
                    "lib/arm64-v8a/libil2cpp.so", MODE}
        if not required <= members:
            raise ValueError("Missing complete game or PGS runtime entries")
        if any(name.startswith("assets/pgrazor/") for name in names):
            raise ValueError("Legacy and migrated runtime layouts must not be mixed")
        manifest = read_bounded(archive, "AndroidManifest.xml", 8 * 1024 * 1024)
        identity = axml.inspect_manifest(manifest)
        if (identity["package"] != pgs_update.GAME_PACKAGE or identity["split"] is not None
                or identity["applications"] != 1 or identity["versionName"] != game_version
                or identity["versionCode"] != expected_code):
            raise ValueError("Unexpected Android package, game version or versionCode")
        expected_provider = {"name": "dev.pgs.BootstrapProvider", "exported": False,
                             "authorities": pgs_update.GAME_PACKAGE + ".pgs.bootstrap"}
        providers = [p for p in identity["providers"]
                     if p["name"] in ("dev.pgs.BootstrapProvider", "dev.pgrazor.BootstrapProvider")]
        if providers != [expected_provider]:
            raise ValueError("Bootstrap manifest identity mismatch")
        if any(a["name"] in ("dev.pgs.GoogleAuthActivity", "dev.pgrazor.GoogleAuthActivity")
               for a in identity["activities"]):
            raise ValueError("Experimental OAuth callback is not permitted in a new candidate")
        _, chunks, pool, _, _ = axml._parse(manifest)
        labels = [attrs.get((axml.ANDROID_NS, "label"))
                  for _, event, name, attrs, depth in axml._walk(chunks, pool)
                  if event == "start" and name == "application" and depth == 1]
        if labels != ["Pok\u00e9mon GO"]:
            raise ValueError("Installed application label must remain Pok\u00e9mon GO")
        mode = json.loads(read_bounded(archive, MODE, 256 * 1024))
        if not isinstance(mode, dict) or mode.get("pgsVersion") != tag or ("pgrazorVersion" in mode and mode["pgrazorVersion"] != tag):
            raise ValueError("PGS mode version differs from the requested release")
        if mode.get("googleBrowserLogin", False) is not False:
            raise ValueError("Experimental OAuth must stay disabled pending authorized PGS configuration")
        if mode.get("compiledGameplay") is not True or mode.get("gadget") is not False:
            raise ValueError("Expected a complete compiled PGS runtime")
        abis = mode.get("runtimeAbis")
        if (not isinstance(abis, list) or not all(isinstance(a, str) for a in abis)
                or len(abis) != len(set(abis)) or "arm64-v8a" not in abis
                or not set(abis) <= MACHINES.keys()):
            raise ValueError("Invalid PGS runtime ABI list")
        verify_elf(archive, "lib/arm64-v8a/libil2cpp.so", MACHINES["arm64-v8a"])
        for abi in abis:
            for library in ("libpgs-core.so", "libpgs-art.so"):
                name = "assets/pgs/" + abi + "/" + library
                if name not in members:
                    raise ValueError("Missing PGS library: " + name)
                verify_elf(archive, name, MACHINES[abi])
        controls = []
        for name in names:
            if not re.fullmatch(r"classes\d*\.dex", name):
                continue
            dex = read_bounded(archive, name, MAX_DEX_BYTES)
            if not dex.startswith(b"dex\n"):
                raise ValueError("Invalid DEX header: " + name)
            if b"Ldev/pgrazor/Control;" in dex:
                raise ValueError("Legacy controls DEX in migrated candidate")
            if REQUIRED_CLASSES[1] in dex:
                if not all(marker in dex for marker in REQUIRED_CLASSES):
                    raise ValueError("Incomplete PGS controls DEX")
                controls.append(name)
        if len(controls) != 1:
            raise ValueError("Expected one complete PGS controls DEX")
    return {
        "status": "STATIC_CANDIDATE_CHECKS_PASSED",
        "apk": apk.name,
        "release_asset": "PGS." + tag + ".apk",
        "bytes": apk.stat().st_size,
        "sha256": pgs_update.sha256(apk),
        "pgs_version": tag,
        "game_version": game_version,
        "game_version_code": game_version_code,
        "package": pgs_update.GAME_PACKAGE,
        "installed_name": "Pok\u00e9mon GO",
        "previous_version_code": previous_version_code,
        "version_code": expected_code,
        "signing_certificate_sha256": pgs_update.PGS_SIGNER,
        "controls_dex": controls[0],
        "runtime_abis": abis,
        "device_tested": False,
        "in_place_update_tested": False,
        "publish_ready": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apk", type=Path)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--game-version", required=True)
    parser.add_argument("--game-version-code", type=int, required=True)
    parser.add_argument("--previous-version-code", type=int, required=True)
    args = parser.parse_args()
    result = verify(args.apk, tag=args.tag, game_version=args.game_version,
                    game_version_code=args.game_version_code,
                    previous_version_code=args.previous_version_code)
    print(json.dumps(result, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
