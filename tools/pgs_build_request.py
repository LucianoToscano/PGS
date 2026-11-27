"""Strict, commit-scoped request for a signed PGS candidate; no credentials."""
import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import subprocess

from game_update import current_profile

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "LucianoToscano/PGS"
REQUEST_PATH = "build-request.json"
MAX_CODE = 2_100_000_000
TAG = re.compile(r"v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")
SHA256 = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True)
class BuildRequest:
    tag: str
    previous_tag: str
    previous_code: int
    expected_code: int
    previous_apk_sha256: str
    retain: bool

    @property
    def asset(self):
        return "PGS." + self.tag + ".apk"

    @property
    def root_asset(self):
        return "PGS." + self.tag + "-Root.apk"

    @property
    def module_asset(self):
        return "PGS." + self.tag + "-Root-module.zip"

    @property
    def names(self):
        return (self.asset, self.root_asset, self.module_asset, "PGS.json",
                "build-info.json", "root-build-info.json", "SHA256SUMS.txt")


def parse_request(data, previous_version, ledger, profile):
    if not isinstance(data, dict) or type(data.get("schema")) is not int or data["schema"] != 1:
        raise ValueError("Unsupported build request schema")
    if data == {"schema": 1, "enabled": False} and data["enabled"] is False:
        return None
    keys = {"schema", "enabled", "version", "previous_version_code",
            "previous_apk_sha256", "game_version", "game_version_code",
            "input_sha256", "authorized_input", "retain_authorized_candidate"}
    if (set(data) != keys or data["enabled"] is not True
            or data["authorized_input"] is not True
            or type(data["retain_authorized_candidate"]) is not bool):
        raise ValueError("Build request must explicitly authorize input and select draft retention")
    previous_tag = previous_version if previous_version.startswith("v") else "v" + previous_version
    previous = TAG.fullmatch(previous_tag)
    if not previous:
        raise ValueError("Invalid previous PGS version")
    major, minor, patch = map(int, previous.groups())
    target = f"v{major}.{minor}.{patch + 1}"
    if data["version"] != target:
        raise ValueError("Requested version must be the next patch after the verified ledger version")
    code = data["previous_version_code"]
    game_code = data["game_version_code"]
    if (type(code) is not int or code != ledger or not 1 <= code < MAX_CODE
            or type(game_code) is not int or not 1 <= game_code < MAX_CODE):
        raise ValueError("Build request versionCode differs from the release ledger")
    if (data["game_version"] != profile["game_version"]
            or game_code != profile["version_code"]
            or data["input_sha256"] != profile["input_sha256"]):
        raise ValueError("Requested original game profile does not match the pinned authorized profile")
    digest = data["previous_apk_sha256"]
    if not isinstance(digest, str) or not SHA256.fullmatch(digest):
        raise ValueError("Previous verified APK digest is required")
    expected = max(code + 1, game_code)
    if expected >= MAX_CODE:
        raise ValueError("Android versionCode limit reached")
    return BuildRequest(target, previous_tag, code, expected, digest,
                        data["retain_authorized_candidate"])


def load_request(root=ROOT):
    data = json.loads((root / REQUEST_PATH).read_text(encoding="utf-8"))
    version = (root / "pgs/VERSION").read_text(encoding="utf-8").strip()
    ledger = int((root / "pgs/PGS_LAST_VERSION_CODE").read_text(encoding="utf-8").strip())
    return parse_request(data, version, ledger, current_profile())


def authorize(request, env):
    if (request is None or env.get("GITHUB_REPOSITORY") != REPOSITORY
            or env.get("GITHUB_REF") != "refs/heads/main"
            or not re.fullmatch(r"[0-9a-f]{40}", env.get("GITHUB_SHA", ""))):
        raise ValueError("Build requires an explicit request on the canonical PGS main branch")
    event = env.get("GITHUB_EVENT_NAME")
    if event == "push":
        return request.retain
    if event == "workflow_dispatch" and env.get("PGS_MANUAL_AUTHORIZED") == "true":
        return request.retain and env.get("PGS_MANUAL_RETAIN") == "true"
    raise ValueError("Unauthorized build event or missing manual input authorization")


def check_changed_request(env, root=ROOT):
    """The automatic path must change the request in the triggering main push."""
    if env.get("GITHUB_EVENT_NAME") != "push":
        return
    payload = json.loads(Path(env["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
    before, after = payload.get("before"), payload.get("after")
    if (not isinstance(before, str) or not re.fullmatch(r"[0-9a-f]{40}", before)
            or before == "0" * 40 or after != env["GITHUB_SHA"]):
        raise ValueError("Invalid or unbound push event")
    diff = subprocess.run(["git", "diff", "--quiet", before, after, "--", REQUEST_PATH],
                          cwd=root, capture_output=True, check=False)
    if diff.returncode != 1:
        raise ValueError("Automatic build requires an actual change to the committed build request")


def gate(env):
    request = load_request()
    if request is None:
        values = {"enabled": "false"}
    else:
        retain = authorize(request, env)
        check_changed_request(env)
        values = {"enabled": "true", "version": request.tag,
                  "previous_code": str(request.previous_code),
                  "expected_code": str(request.expected_code),
                  "retain": str(retain).lower()}
    with Path(env["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as out:
        for key, value in values.items():
            out.write(f"{key}={value}\n")
    print("Build request accepted" if request else "No build requested")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--gate", action="store_true")
    mode.add_argument("--ci-version", action="store_true")
    args = parser.parse_args()
    try:
        if args.gate:
            gate(os.environ)
        else:
            request = load_request()
            previous = (ROOT / "pgs/VERSION").read_text(encoding="utf-8").strip()
            print(request.tag if request else (previous if previous.startswith("v") else "v" + previous))
    except (ValueError, OSError, KeyError, TypeError):
        raise SystemExit("PGS build request validation failed; inspect schema, authorization and verified ledger") from None


if __name__ == "__main__":
    main()
