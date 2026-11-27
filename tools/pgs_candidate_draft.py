"""Opt-in retention of one verified three-variant candidate in an unpublished release.

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
from pgs_build_request import authorize, load_request
from verify_release import verify_signed_candidate

ROOT = Path(__file__).resolve().parents[1]
SIGNER = "d95c6bdfcbd91dc5c9cde698487c88e4994771a475e4efde4567b8d5f44e96cf"


def digest(path):
    with Path(path).open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def authorized_commit(env, request, require_retention=True):
    retain = authorize(request, env)
    if (env.get("PGS_VERSION") != request.tag
            or env.get("PGS_EXPECTED_VERSION_CODE") != str(request.expected_code)
            or env.get("PGS_RETAIN_AUTHORIZED") != str(retain).lower()
            or (require_retention and not retain)):
        raise ValueError("Candidate request does not match the authorized build gate")
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


def require_unused_target(cli, env, request):
    if any(row.get("tag_name") == request.tag for row in releases(cli, env)):
        raise ValueError("Candidate release already exists; never overwrite a previous candidate")
    refs = parse_json(run_gh(cli, env, ["api", f"repos/{REPOSITORY}/git/matching-refs/tags/{request.tag}"]))
    if not isinstance(refs, list) or any(not isinstance(row, dict) for row in refs):
        raise ValueError("Unexpected tag metadata")
    if any(row.get("ref") == "refs/tags/" + request.tag for row in refs):
        raise ValueError("Candidate tag already exists; never reuse an existing tag")


def require_previous_candidate(cli, env, request):
    """Bind the next allocation to the previous verified signed candidate."""
    matches = [row for row in releases(cli, env) if row.get("tag_name") == request.previous_tag]
    if len(matches) != 1:
        raise ValueError("Previous candidate release is missing or ambiguous")
    assets = matches[0].get("assets")
    if not isinstance(assets, list):
        raise ValueError("Previous candidate assets are missing")
    def asset(name):
        rows = [a for a in assets if isinstance(a, dict) and a.get("name") == name]
        if (len(rows) != 1 or rows[0].get("state") != "uploaded"
                or type(rows[0].get("id")) is not int or rows[0]["id"] <= 0):
            raise ValueError("Previous candidate asset is missing or incomplete")
        return rows[0]
    apk = asset("PGS." + request.previous_tag + ".apk")
    receipt_asset = asset("PGS.json")
    if (apk.get("digest") != "sha256:" + request.previous_apk_sha256
            or type(apk.get("size")) is not int or apk["size"] <= 100_000_000
            or type(receipt_asset.get("size")) is not int
            or not 0 < receipt_asset["size"] <= 65536):
        raise ValueError("Previous verified APK metadata differs from request")
    receipt = parse_json(run_gh(cli, env, ["api", "-H", "Accept: application/octet-stream",
                         f"repos/{REPOSITORY}/releases/assets/{receipt_asset['id']}"]))
    if (not isinstance(receipt, dict)
            or receipt.get("pgs_version") != request.previous_tag
            or receipt.get("release_asset") != apk["name"]
            or receipt.get("version_code") != request.previous_code
            or receipt.get("sha256") != request.previous_apk_sha256
            or receipt.get("bytes") != apk["size"]
            or receipt.get("signing_certificate_sha256") != SIGNER):
        raise ValueError("Previous candidate receipt is inconsistent with ledger, APK or signer")


def safe_file(folder, name):
    path = folder / name
    if not path.is_file() or path.is_symlink():
        raise ValueError("Missing or unsafe candidate file: " + name)
    return path


def stage_bundle(source, target, profile, commit, verifier, request):
    apk = safe_file(source, "PGS.apk")
    receipt_path = safe_file(source, "PGS.json")
    info_path = safe_file(source, "build-info.json")
    safe_file(source, "SHA256SUMS.txt")
    root_apk = safe_file(source, "PGS-Root.apk")
    root_module = safe_file(source, "PGS-Root-module.zip")
    root_info = safe_file(source, "root-build-info.json")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    info = json.loads(info_path.read_text(encoding="utf-8"))
    verified = verifier(apk, tag=request.tag, game_version=profile["game_version"],
                        game_version_code=profile["version_code"], previous_version_code=request.previous_code)
    if (receipt != verified or receipt.get("release_asset") != request.asset
            or receipt.get("version_code") != request.expected_code):
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
    if sha != receipt["sha256"] or apk.stat().st_size != receipt["bytes"]:
        raise ValueError("Candidate checksum or size differs from its receipts")
    actual = verify_signed_candidate(source, request.tag, commit)
    downloads = ((apk, request.asset), (root_apk, request.root_asset),
                 (root_module, request.module_asset))
    for path, name in downloads:
        shutil.copyfile(path, target / name)
        if digest(target / name) != actual[path.name]:
            raise ValueError("Staged download differs from verified source")
    shutil.copyfile(receipt_path, target / "PGS.json")
    shutil.copyfile(info_path, target / "build-info.json")
    shutil.copyfile(root_info, target / "root-build-info.json")
    (target / "SHA256SUMS.txt").write_text(
        "".join(actual[path.name] + "  " + name + "\n" for path, name in downloads),
        encoding="utf-8")
    return {name: {"size": (target / name).stat().st_size,
                   "digest": "sha256:" + digest(target / name)} for name in request.names}


def verify_retained(rows, expected, commit, request):
    matches = [row for row in rows if row.get("tag_name") == request.tag]
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


def retain(cli, env, source, profile, commit, verifier, request):
    require_unused_target(cli, env, request)
    with tempfile.TemporaryDirectory(prefix="pgs-candidate-draft-", dir=source.parent) as directory:
        target = Path(directory)
        expected = stage_bundle(source, target, profile, commit, verifier, request)
        require_unused_target(cli, env, request)
        run_gh(cli, env, ["release", "create", request.tag, "--repo", REPOSITORY,
               "--draft", "--target", commit, "--title", "PGS " + request.tag + " - device test candidate",
               "--notes", "UNPUBLISHED Root and Non-Root candidate. Static bundle checks passed. Device test and in-place update test pending. Not approved for distribution. Source: " + commit,
               *[str(target / name) for name in request.names]], timeout=600)
        verify_retained(releases(cli, env), expected, commit, request)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    try:
        request = load_request()
        commit = authorized_commit(os.environ, request, require_retention=not args.preflight)
        cli, env = github_env()
        if args.preflight:
            require_previous_candidate(cli, env, request)
            require_unused_target(cli, env, request)
            print("Previous signed candidate verified; requested draft target is unused")
            return
        profile = current_profile()
        sys.path.insert(0, str(ROOT / "pgs"))
        import pgs_candidate
        source = Path(os.environ["RUNNER_TEMP"]) / "pgs-candidate-validation"
        retain(cli, env, source, profile, commit, pgs_candidate.verify, request)
        print("Verified candidate retained in unpublished draft:", request.tag)
    except (ValueError, OSError, KeyError, TypeError):
        # No remote response bodies, token values, or authenticated URLs in logs.
        raise SystemExit("Candidate retention failed; check authorization, draft uniqueness, and receipt/asset integrity. Do not publish or overwrite a partial draft.") from None


if __name__ == "__main__":
    main()
