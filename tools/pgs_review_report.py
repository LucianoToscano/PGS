"""Classify changed paths for the PGS review process; never modify files."""
import argparse
import json
from pathlib import PurePosixPath
import re
import subprocess


def revision(value):
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise ValueError("Expected a complete Git commit SHA")
    return value


def category(path):
    parts = PurePosixPath(path).parts
    if path == "LICENSE" or path == "THIRD_PARTY.md" or "licenses" in parts:
        return "license"
    if path.startswith(".github/workflows/") or path.startswith("tools/"):
        return "automation"
    if path.startswith(("pgrazor/native/", "pgrazor/art/", "pgrazor/zygisk/")):
        return "native"
    if path.startswith(("pgrazor/src/", "pgrazor/root-installer/")) or path.endswith("AndroidManifest.xml"):
        return "android"
    if path.startswith("pgrazor/test/"):
        return "tests"
    if path.startswith("website/"):
        return "website"
    if path.startswith("docs/") or path.endswith(".md"):
        return "documentation"
    if path.startswith("pgrazor/"):
        return "build_or_runtime"
    return "other"


def report(paths):
    counts = {}
    for path in set(paths):
        key = category(path)
        counts[key] = counts.get(key, 0) + 1
    reviews = sorted(key for key in counts if key in {
        "license", "automation", "native", "android", "build_or_runtime", "other"
    })
    return {
        "changed_paths": sum(counts.values()),
        "categories": dict(sorted(counts.items())),
        "specialist_review_categories": reviews,
        "automatic_merge": False,
        "automatic_code_changes": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, type=revision)
    parser.add_argument("--head", required=True, type=revision)
    args = parser.parse_args()
    raw = subprocess.check_output(["git", "diff", "--name-only", "--no-renames",
                                   "-z", args.base + "..." + args.head, "--"])
    paths = [item.decode("utf-8", errors="surrogateescape")
             for item in raw.split(b"\0") if item]
    print(json.dumps(report(paths), indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
