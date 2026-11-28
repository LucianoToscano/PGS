"""Read-only upstream revision monitor; never downloads source or merges branches."""
import argparse
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
REF = "refs/heads/main"


def read_origin(notice):
    """Read the actual original repository and reviewed baseline from legal provenance."""
    fields = {}
    for line in notice.read_text(encoding="utf-8").splitlines():
        for label in ("Original source", "Upstream baseline"):
            if line.startswith(label + ": "):
                if label in fields:
                    raise ValueError("Duplicate provenance entry")
                fields[label] = line.split(": ", 1)[1].strip()
    url = fields.get("Original source", "")
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.netloc != "github.com"
            or parsed.query or parsed.fragment
            or not re.fullmatch(r"/[A-Za-z0-9-]+/[A-Za-z0-9_.-]+", parsed.path)
            or any(part in (".", "..") for part in parsed.path.split("/"))):
        raise ValueError("Expected a public GitHub origin in NOTICE")
    baseline = fields.get("Upstream baseline", "")
    if not re.fullmatch(r"[0-9a-f]{40}", baseline):
        raise ValueError("Invalid reviewed baseline in NOTICE")
    return url.removesuffix(".git") + ".git", baseline


UPSTREAM, BASELINE = read_origin(ROOT / "NOTICE")


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
