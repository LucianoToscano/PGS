"""Read-only inventory of current project identity references in Git-tracked text.

The generated snapshot is excluded from its own count. Binary/non-UTF-8
files, symlinks and submodule entries are not read as text. Matching source
lines are never printed. Case-insensitive matching includes identifiers,
comments and intentional compatibility references.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = "docs/PGS_REMAINING_REFERENCES.json"
IDENTITY = re.compile(r"pgs", re.IGNORECASE)
FILE_LEGACY = re.compile("pg" + "razor", re.IGNORECASE)

ABBREVIATIONS = re.compile(r"\b(?:PGS_[A-Z0-9_]+|pgs_[A-Za-z0-9_]+|Pgs[A-Z][A-Za-z0-9_]*)\b")


def abbreviation_counts(data):
    """Count abbreviated source spellings separately from the original inventory."""
    if b"\0" in data:
        return None
    try:
        source = data.decode("utf-8")
    except UnicodeDecodeError:
        return None
    counts = Counter()
    for match in ABBREVIATIONS.findall(source):
        form = "uppercase" if match.startswith("PGS_") else ("lowercase" if match.startswith("pgs_") else "camelcase")
        counts[form] += 1
    return dict(sorted(counts.items()))


def text_count(data):
    if b"\0" in data:
        return None
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None
    return len(IDENTITY.findall(text))


def index_blobs(root, tracked):
    """Read exact staged bytes with one Git process, independent of checkout filters."""
    with subprocess.Popen(["git", "cat-file", "--batch"], cwd=root,
                          stdin=subprocess.PIPE, stdout=subprocess.PIPE) as git:
        for path, (mode, oid) in sorted(tracked.items()):
            if mode not in (b"100644", b"100755"):
                continue
            git.stdin.write(oid + b"\n")
            git.stdin.flush()
            header = git.stdout.readline().split()
            if len(header) != 3 or header[0] != oid or header[1] != b"blob":
                raise ValueError("Cannot read indexed blob: " + path)
            size = int(header[2])
            data = git.stdout.read(size)
            if len(data) != size or git.stdout.read(1) != b"\n":
                raise ValueError("Incomplete indexed blob: " + path)
            yield path, data
        git.stdin.close()
        if git.wait() != 0:
            raise ValueError("Git blob scan failed")


def worktree_blobs(root, tracked):
    for path, (mode, _) in sorted(tracked.items()):
        if mode not in (b"100644", b"100755"):
            continue
        target = root / path
        if target.is_symlink() or not target.is_file():
            raise ValueError("Tracked regular file missing or replaced: " + path)
        yield path, target.read_bytes()


def scan(root=ROOT, *, worktree=False):
    root = Path(root)
    raw = subprocess.check_output(["git", "ls-files", "--stage", "-z"], cwd=root)
    tracked = {}
    for item in raw.split(b"\0"):
        if not item:
            continue
        metadata, name = item.split(b"\t", 1)
        mode, oid, stage = metadata.split()
        if stage != b"0":
            raise ValueError("Cannot audit an unmerged index")
        path = name.decode("utf-8")
        if path == SNAPSHOT:
            continue
        tracked[path] = (mode, oid)
    previous = json.loads(subprocess.check_output(["git", "show", ":" + SNAPSHOT], cwd=root).decode("utf-8"))
    categories = {row["path"]: row["category"] for row in previous["files"]}
    rows = []
    counts = Counter()
    abbreviation_totals = Counter()
    abbreviation_rows = []
    text_files = 0
    blobs = worktree_blobs(root, tracked) if worktree else index_blobs(root, tracked)
    for path, data in blobs:
        n = text_count(data)
        if n is None:
            continue
        text_files += 1
        abbreviated = abbreviation_counts(data)
        if abbreviated:
            abbreviation_totals.update(abbreviated)
            abbreviation_rows.append({"path": path, "occurrences": sum(abbreviated.values()), "by_form": abbreviated})
        if n:
            category = categories.get(path)
            if category is None:
                if path.startswith("pgs/test/"):
                    category = "tests"
                elif path.startswith(".github/workflows/"):
                    category = "workflows"
                elif path.startswith("pgs/native/"):
                    category = "native"
                elif path.startswith("docs/"):
                    category = "documentation"
                else:
                    category = "other"
            rows.append({"path": path, "category": category, "occurrences": n})
            counts[category] += n
    return {
        "scope": ("Working-tree copies of Git-tracked regular UTF-8 text" if worktree
                  else "Git-indexed regular UTF-8 text") + ", excluding NUL-containing files and the snapshot itself",
        "tracked_files": len(tracked),
        "text_files": text_files,
        "remaining_files": len(rows),
        "remaining_occurrences": sum(counts.values()),
        "remaining_by_category": dict(sorted(counts.items())),
        "tracked_name_matches": [p for p in sorted(tracked) if FILE_LEGACY.search(p)],
        "files": rows,
        "abbreviations": {
            "remaining_files": len(abbreviation_rows),
            "remaining_occurrences": sum(abbreviation_totals.values()),
            "by_form": dict(sorted(abbreviation_totals.items())),
            "tracked_name_matches": [p for p in sorted(tracked) if ABBREVIATIONS.search(p)],
            "files": abbreviation_rows,
        },
    }


def snapshot_differences(previous, current):
    """Return path/count differences only, without matching source lines."""
    old = {row["path"]: row["occurrences"] for row in previous["files"]}
    new = {row["path"]: row["occurrences"] for row in current["files"]}
    return [{"path": path, "snapshot": old.get(path, 0), "actual": new.get(path, 0)}
            for path in sorted(old.keys() | new.keys())
            if old.get(path, 0) != new.get(path, 0)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", action="store_true", help="Omit per-file rows")
    parser.add_argument("--compare-snapshot", action="store_true",
                        help="Include per-file count differences against the checked-in snapshot")
    parser.add_argument("--worktree", action="store_true",
                        help="Inspect checkout bytes instead of indexed Git blobs")
    args = parser.parse_args()
    result = scan(worktree=args.worktree)
    if args.compare_snapshot:
        previous = json.loads(subprocess.check_output(["git", "show", ":" + SNAPSHOT], cwd=ROOT).decode("utf-8"))
        result["snapshot_differences"] = snapshot_differences(previous, result)
    if args.summary:
        result.pop("files")
        result["abbreviations"].pop("files")
    print(json.dumps(result, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
