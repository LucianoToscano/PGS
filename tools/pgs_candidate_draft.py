"""Opt-in retention of one verified candidate in an unpublished release.

The default validation workflow remains receipt-only. No source input, signing
material, unverified APK, or public workflow artifact is retained by this tool.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from game_update import current_profile
from pgs_pinned_input import github_env, REPOSITORY

ROOT = Path(__file__).resolve().parents[1]
TAG = "v0.0.4"
PREVIOUS_CODE = 2026111606
ASSET = "PGS." + TAG + ".apk"
NAMES = (ASSET, "PGS.json", "build-info.json", "SHA256SUMS.txt")


def digest(path):
    with Path(path).open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def authorized_commit(env):
    if (env.get("PGS_RETAIN_AUTHORIZED") != "true"
            or env.get("GITHUB_REPOSITORY") != REPOSITORY
            or env.get("GITHUB_EVENT_NAME") != "workflow_dispatch"
            or env.get("GITHUB_REF") != "refs/heads/main"
            or not re.fullmatch(r"[0-9a-f]{40}", env.get("GITHUB_SHA", ""))):
        raise ValueError("Candidate retention requires explicit authorization on PGS main")
    return env["GITHUB_SHA"]


def run_gh(cli, env, args, timeout=60):
    try:
        result = subprocess.run([cli, *args], env=env, capture_output=True,
                                text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise ValueError("GitHub draft operation failed or timed out") from None
    if result.returncode:
        raise ValueError("GitHub draft operation failed; inspect the existing draft before retrying")
    return result.stdout


def parse_json(raw):
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        raise ValueError("Invalid GitHub release metadata") from None


def releases(cli, env):
    pages = parse_json(run_gh(cli, env, ["api", "--paginate", "--slurp",
                       f"repos/{REPOSITORY}/releases?per_page=100"]))
    if not isinstance(pages, list) or any(not isinstance(page, list) for page in pages):
        raise ValueError("Unexpected release listing")
    rows = [row for page in pages for row in page]
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError("Unexpected release entry")
    return rows


def require_unused_target(cli, env):
    if any(row.get("tag_name") == TAG for row in releases(cli, env)):
        raise ValueError("Candidate release already exists; never overwrite a previous candidate")
    refs = parse_json(run_gh(cli, env, ["api", f"repos/{REPOSITORY}/git/matching-refs/tags/{TAG}"]))
    if not isinstance(refs, list) or any(not isinstance(row, dict) for row in refs):
        raise ValueError("Unexpected tag metadata")
    if any(row.get("ref") == "refs/tags/" + TAG for row in refs):
        raise ValueError("Candidate tag already exists; never reuse an existing tag")


def safe_file(folder, name):
    path = folder / name
    if not path.is_file() or path.is_symlink():
        raise ValueError("Missing or unsafe candidate file: " + name)
    return path


def stage_bundle(source, target, profile, commit, verifier):
    apk = safe_file(source, "PGS.apk")
    receipt_path = safe_file(source, "PGS.json")
    info_path = safe_file(source, "build-info.json")
    sums_path = safe_file(source, "SHA256SUMS.txt")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    info = json.loads(info_path.read_text(encoding="utf-8"))
    verified = verifier(apk, tag=TAG, game_version=profile["game_version"],
                        game_version_code=profile["version_code"], previous_version_code=PREVIOUS_CODE)
    if receipt != verified or receipt.get("release_asset") != ASSET:
        raise ValueError("Candidate receipt differs from independent APK verification")
    if (receipt.get("status") != "STATIC_CANDIDATE_CHECKS_PASSED"
            or any(receipt.get(key) is not False for key in
                   ("device_tested", "in_place_update_tested", "publish_ready"))
            or info.get("source_commit") != commit or info.get("device_tested") is not False
            or info.get("game_version") != profile["game_version"]
            or info.get("game_version_code") != profile["version_code"]
            or info.get("input_sha256") != profile["input_sha256"]
            or info.get("apk_version_code") != receipt["version_code"]
            or info.get("apk_sha256") != receipt["sha256"]):
        raise ValueError("Build receipts do not describe this untested candidate and source commit")
    sha = digest(apk)
    if (sha != receipt["sha256"] or apk.stat().st_size != receipt["bytes"]
            or sums_path.read_text(encoding="utf-8").split() != [sha, "PGS.apk"]):
        raise ValueError("Candidate checksum or size differs from its receipts")
    shutil.copyfile(apk, target / ASSET)
    shutil.copyfile(receipt_path, target / "PGS.json")
    shutil.copyfile(info_path, target / "build-info.json")
    (target / "SHA256SUMS.txt").write_text(sha + "  " + ASSET + "\n", encoding="utf-8")
    return {name: {"size": (target / name).stat().st_size,
                   "digest": "sha256:" + digest(target / name)} for name in NAMES}


def verify_retained(rows, expected, commit):
    matches = [row for row in rows if row.get("tag_name") == TAG]
    if len(matches) != 1 or matches[0].get("draft") is not True:
        raise ValueError("Retained candidate must be exactly one unpublished draft")
    row = matches[0]
    if row.get("target_commitish") != commit:
        raise ValueError("Retained candidate source commit mismatch")
    assets = row.get("assets")
    if not isinstance(assets, list) or len(assets) != len(expected):
        raise ValueError("Unexpected retained asset count")
    actual = {}
    for asset in assets:
        if not isinstance(asset, dict) or asset.get("state") != "uploaded":
            raise ValueError("Retained asset is incomplete")
        name = asset.get("name")
        if name not in expected or name in actual:
            raise ValueError("Unexpected or duplicate retained asset")
        actual[name] = {"size": asset.get("size"), "digest": asset.get("digest")}
    if actual != expected:
        raise ValueError("Retained draft asset digests differ from verified local files")


def retain(cli, env, source, profile, commit, verifier):
    require_unused_target(cli, env)
    with tempfile.TemporaryDirectory(prefix="pgs-candidate-draft-", dir=source.parent) as directory:
        target = Path(directory)
        expected = stage_bundle(source, target, profile, commit, verifier)
        require_unused_target(cli, env)
        run_gh(cli, env, ["release", "create", TAG, "--repo", REPOSITORY,
               "--draft", "--target", commit, "--title", "PGS " + TAG + " - device test candidate",
               "--notes", "UNPUBLISHED candidate. Static checks passed. Device test and in-place update test pending. Not approved for distribution. Source: " + commit,
               *[str(target / name) for name in NAMES]], timeout=600)
        verify_retained(releases(cli, env), expected, commit)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    try:
        commit = authorized_commit(os.environ)
        cli, env = github_env()
        if args.preflight:
            require_unused_target(cli, env)
            print("Candidate draft target is unused")
            return
        profile = current_profile()
        if (ROOT / "pgs/PGS_LAST_VERSION_CODE").read_text(encoding="utf-8").strip() != str(PREVIOUS_CODE):
            raise ValueError("Release ledger changed; prepare a new candidate version")
        sys.path.insert(0, str(ROOT / "pgs"))
        import pgs_candidate
        source = Path(os.environ["RUNNER_TEMP"]) / "pgs-v004-validation"
        retain(cli, env, source, profile, commit, pgs_candidate.verify)
        print("Verified candidate retained in unpublished draft:", TAG)
    except (ValueError, OSError, KeyError, TypeError):
        # No remote response bodies, token values, or authenticated URLs in logs.
        raise SystemExit("Candidate retention failed; check authorization, draft uniqueness, and receipt/asset integrity. Do not publish or overwrite a partial draft.") from None


if __name__ == "__main__":
    main()
