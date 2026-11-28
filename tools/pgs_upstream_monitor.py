"""Read-only upstream revision monitor; never downloads source or merges branches."""
import argparse
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

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


def compare_url(reviewed, current):
    path = urlsplit(UPSTREAM).path.removesuffix(".git")
    return "https://api.github.com/repos" + path + "/compare/" + revision(reviewed) + "..." + revision(current) + "?per_page=100"


def comparison_summary(data, reviewed, current, root=ROOT):
    """Summarize comparison metadata only; never use patches or upstream code."""
    if data.get("base_commit", {}).get("sha") != reviewed:
        raise ValueError("Upstream comparison base differs from the reviewed revision")
    status = data.get("status")
    if status not in ("ahead", "behind", "diverged", "identical"):
        raise ValueError("Unexpected comparison status")
    for field in ("ahead_by", "behind_by", "total_commits"):
        if type(data.get(field)) is not int or data[field] < 0:
            raise ValueError("Invalid comparison count")
    if current != reviewed and status == "identical":
        raise ValueError("Different revisions cannot have an identical comparison status")
    commits = []
    for row in data["commits"]:
        sha = revision(row["sha"])
        subject = row["commit"]["message"].splitlines()
        subject = (subject[0] if subject else "")[:240]
        lower = subject.lower()
        category = ("fix" if re.search(r"\b(fix(?:es|ed)?|correct(?:ion|ed)?|repair|resolve)\b", lower)
                    else "feature" if re.search(r"\b(add(?:ed)?|feature|support|introduce|implement)\b", lower)
                    else "other")
        commits.append({"sha": sha, "subject": subject, "category_hint": category})
    files = []
    upstream_identity = urlsplit(UPSTREAM).path.rsplit("/", 1)[1].removesuffix(".git")
    for row in data["files"]:
        name = row["filename"]
        if not isinstance(name, str) or not name or name.startswith("/") or ".." in name.split("/"):
            raise ValueError("Invalid comparison filename")
        local = re.sub(re.escape(upstream_identity), "pgs", name, flags=re.IGNORECASE)
        local = local if (root / local).is_file() else None
        high = name.startswith(".github/") or "/native/" in name or "/src/" in name or name.endswith(("build.py", "release_apk.py"))
        files.append({"path": name, "status": row["status"], "additions": row["additions"],
                      "deletions": row["deletions"], "local_path": local,
                      "review_priority": "high" if high else "normal"})
    return {"comparison_status": status, "ahead_by": data["ahead_by"], "behind_by": data["behind_by"],
            "total_commits": data["total_commits"], "commits": commits, "files": files,
            "commit_list_may_be_truncated": len(commits) < data["total_commits"],
            "file_list_may_be_truncated": len(files) >= 300,
            "conflicts_confirmed": False,
            "review_note": "Categories are message-based hints. Existing local paths are review candidates, not proven conflicts."}


def compare_metadata(reviewed, current):
    if reviewed == current:
        return {"comparison_status": "identical", "ahead_by": 0, "behind_by": 0, "total_commits": 0,
                "commits": [], "files": [], "commit_list_may_be_truncated": False,
                "file_list_may_be_truncated": False, "conflicts_confirmed": False}
    url = compare_url(reviewed, current)
    request = Request(url, headers={"Accept": "application/vnd.github+json",
                                    "User-Agent": "PGS-read-only-monitor",
                                    "X-GitHub-Api-Version": "2022-11-28"})
    with urlopen(request, timeout=20) as response:
        raw = response.read(16 * 1024 * 1024 + 1)
    if len(raw) > 16 * 1024 * 1024:
        raise ValueError("Comparison metadata exceeds safe response limit")
    return comparison_summary(json.loads(raw), reviewed, current)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviewed", default=BASELINE)
    args = parser.parse_args()
    reviewed = revision(args.reviewed)
    result = subprocess.run(
        ["git", "ls-remote", "--exit-code", UPSTREAM, REF],
        capture_output=True, text=True, check=True, timeout=30,
    )
    current = parse_remote(result.stdout)
    report = receipt(current, reviewed)
    report.update(compare_metadata(reviewed, current))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
