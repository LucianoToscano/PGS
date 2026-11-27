"""Read-only upstream revision monitor; never downloads source or merges branches."""
import argparse
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = "https://github.com/jpitty03/PGRazor.git"
REF = "refs/heads/main"
BASELINE = "1106592aa045759f55f594ff6968f783ff636fe9"


def revision(value):
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise ValueError("Invalid Git revision")
    return value


def parse_remote(output):
    lines = output.strip().splitlines()
    if len(lines) != 1:
        raise ValueError("Expected exactly one upstream ref")
    fields = lines[0].split()
    if len(fields) != 2 or fields[1] != REF:
        raise ValueError("Unexpected upstream ref")
    return revision(fields[0])


def receipt(current, reviewed=BASELINE):
    current, reviewed = revision(current), revision(reviewed)
    return {
        "upstream": UPSTREAM,
        "ref": REF,
        "reviewed_revision": reviewed,
        "current_revision": current,
        "status": "unchanged" if current == reviewed else "review_required",
        "source_modified": False,
        "merge_performed": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviewed", default=BASELINE)
    args = parser.parse_args()
    reviewed = revision(args.reviewed)
    result = subprocess.run(
        ["git", "ls-remote", "--exit-code", UPSTREAM, REF],
        capture_output=True, text=True, check=True, timeout=30,
    )
    print(json.dumps(receipt(parse_remote(result.stdout), reviewed), indent=2))


if __name__ == "__main__":
    main()
