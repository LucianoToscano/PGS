"""Retrieve an authorized, hash-pinned original from this repository's unpublished draft.

No external token, URL secret, release mutation, or publication is performed.
The archive is never a workflow artifact. Only the approved profile is accepted.
"""
import argparse
import base64
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

from game_update import current_profile, verify_input
from private_input import required_setting

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "LucianoToscano/PGS"
RELEASE_TAG = "build-inputs"
EXPECTED_BYTES = {"0.439.0": 169083658}


def expected_asset(profile):
    version = profile["game_version"]
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version) or version not in EXPECTED_BYTES:
        raise ValueError("No authorized archive size recorded for the selected game profile")
    return f"Pokemon_GO_{version}_ARM64_ORIGINAL.apkm", EXPECTED_BYTES[version]


def resolve_asset(pages, profile):
    """Only one exact draft and one exact uploaded, pinned asset are accepted."""
    name, size = expected_asset(profile)
    if not isinstance(pages, list) or any(not isinstance(page, list) for page in pages):
        raise ValueError("Unexpected GitHub release metadata")
    releases = [r for page in pages for r in page
                if isinstance(r, dict) and r.get("tag_name") == RELEASE_TAG]
    if len(releases) != 1 or releases[0].get("draft") is not True:
        raise ValueError("Create and keep the authorized build-inputs release in draft status")
    assets = releases[0].get("assets")
    if not isinstance(assets, list):
        raise ValueError("Missing draft asset metadata")
    matches = [a for a in assets if isinstance(a, dict) and a.get("name") == name]
    if len(matches) != 1:
        raise ValueError("The authorized original archive is missing or ambiguous in build-inputs")
    asset = matches[0]
    if (asset.get("state") != "uploaded" or asset.get("size") != size
            or asset.get("digest") != "sha256:" + profile["input_sha256"]
            or type(asset.get("id")) is not int or asset["id"] <= 0):
        raise ValueError("Draft archive metadata differs from the authorized game profile")
    return asset["id"]


def github_env():
    if os.environ.get("GITHUB_REPOSITORY", REPOSITORY) != REPOSITORY:
        raise ValueError("Draft input access is restricted to the PGS repository")
    cli = shutil.which("gh")
    token = os.environ.get("GH_TOKEN")
    if not cli or not token:
        raise ValueError("Authorized GitHub CLI access is unavailable")
    # The caller's signing secrets must not be passed to the download subprocess.
    env = {k: v for k, v in os.environ.items()
           if not any(term in k.upper() for term in ("KEYSTORE", "KEY_ALIAS", "STORE_PASSWORD", "KEY_PASSWORD"))}
    env["GH_TOKEN"] = token
    return cli, env


def lookup(cli, env, profile):
    try:
        result = subprocess.run(
            [cli, "api", "--paginate", "--slurp",
             f"repos/{REPOSITORY}/releases?per_page=100"],
            env=env, capture_output=True, text=True, timeout=60, check=False)
        if result.returncode:
            raise ValueError("Draft lookup failed; check the authorized repository token and draft visibility")
        pages = json.loads(result.stdout)
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        raise ValueError("Draft release lookup failed or returned invalid metadata") from None
    return resolve_asset(pages, profile)


def fetch_archive(cli, env, profile, folder):
    name, size = expected_asset(profile)
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "game.apkm"
    temporary = folder / (name + ".partial")
    if target.exists() or target.is_symlink() or temporary.exists() or temporary.is_symlink():
        raise ValueError("Input folder must start empty; refusing a stale game archive")
    asset_id = lookup(cli, env, profile)
    created = False
    try:
        with temporary.open("xb") as out:
            created = True
            try:
                result = subprocess.run(
                    [cli, "api", "-H", "Accept: application/octet-stream",
                     f"repos/{REPOSITORY}/releases/assets/{asset_id}"],
                    env=env, stdout=out, stderr=subprocess.DEVNULL,
                    timeout=600, check=False)
            except (OSError, subprocess.TimeoutExpired):
                raise ValueError("Draft archive download failed or timed out") from None
        if result.returncode or temporary.stat().st_size != size:
            raise ValueError("Draft archive download failed or returned unexpected size")
        verified = verify_input(temporary, profile)
        if lookup(cli, env, profile) != asset_id:
            raise ValueError("Draft asset changed during verification")
        if target.exists() or target.is_symlink():
            raise ValueError("Input path changed during verification")
        temporary.replace(target)
        return verified
    finally:
        if created:
            temporary.unlink(missing_ok=True)


def load_key(profile, folder):
    archive = folder / "game.apkm"
    if not archive.is_file() or archive.is_symlink():
        raise ValueError("Authorized original must be verified before loading signing material")
    verify_input(archive, profile)
    raw = base64.b64decode(required_setting("KEYSTORE_BASE64"), validate=True)
    if not raw:
        raise ValueError("Empty signing key")
    key = Path(required_setting("KEYSTORE"))
    key.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(key, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as out:
        out.write(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--load-key", action="store_true")
    args = parser.parse_args()
    try:
        profile = current_profile()
        folder = ROOT / "pgs" / "input"
        if args.load_key:
            load_key(profile, folder)
            print("Existing signer loaded into the runner's isolated key path")
            return
        cli, env = github_env()
        if args.preflight:
            lookup(cli, env, profile)
            print("Authorized draft asset metadata matches the selected game profile")
            return
        verified = fetch_archive(cli, env, profile, folder)
        print("Pinned original verified:", verified["game_version"], verified["sha256"])
    except (ValueError, OSError, KeyError, TypeError) as exc:
        # Controlled ValueError messages contain no secrets or remote response bodies.
        if type(exc) is ValueError:
            raise SystemExit(str(exc)) from None
        raise SystemExit("Private input or signing configuration validation failed") from None


if __name__ == "__main__":
    main()
