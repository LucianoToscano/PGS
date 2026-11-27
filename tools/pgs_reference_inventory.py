"""Read-only inventory of legacy identity references in Git-tracked text.

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
LEGACY = re.compile(r"pgrazor", re.IGNORECASE)


def text_count(data):
    if b"\0" in data:
        return None
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None
    return len(LEGACY.findall(text))


def scan(root=ROOT):
    root = Path(root)
    raw = subprocess.check_output(["git", "ls-files", "--stage", "-z"], cwd=root)
    tracked = {}
    for item in raw.split(b"\0"):
        if not item:
            continue
        metadata, name = item.split(b"\t", 1)
        mode, _, stage = metadata.split()
        if stage != b"0":
            raise ValueError("Cannot audit an unmerged index")
        path = name.decode("utf-8")
        if path == SNAPSHOT:
            continue
        tracked[path] = mode
    previous = json.loads((root / SNAPSHOT).read_text(encoding="utf-8"))
    categories = {row["path"]: row["category"] for row in previous["files"]}
    rows = []
    counts = Counter()
    text_files = 0
    for path, mode in sorted(tracked.items()):
        if mode not in (b"100644", b"100755"):
            continue
        target = root / path
        if target.is_symlink() or not target.is_file():
            raise ValueError("Tracked regular file missing or replaced: " + path)
        n = text_count(target.read_bytes())
        if n is None:
            continue
        text_files += 1
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
        "scope": "Git-tracked regular UTF-8 text, excluding NUL-containing files and the snapshot itself",
        "tracked_files": len(tracked),
        "text_files": text_files,
        "remaining_files": len(rows),
        "remaining_occurrences": sum(counts.values()),
        "remaining_by_category": dict(sorted(counts.items())),
        "tracked_name_matches": [p for p in sorted(tracked) if LEGACY.search(p)],
        "files": rows,
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
    args = parser.parse_args()
    result = scan()
    if args.compare_snapshot:
        previous = json.loads((ROOT / SNAPSHOT).read_text(encoding="utf-8"))
        result["snapshot_differences"] = snapshot_differences(previous, result)
    if args.summary:
        result.pop("files")
    print(json.dumps(result, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
