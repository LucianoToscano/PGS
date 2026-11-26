"""Read-only inventory of legacy project names in tracked source files.

Run from a checkout with Git available. Report paths and counts, never file
contents or environment values. Historical files are reported separately.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
RULES = {
    "java_namespace": re.compile(r"dev[./]pgrazor(?:[./]|\b)"),
    "legacy_env": re.compile(r"\bPGRAZOR_[A-Z0-9_]+"),
    "native_identifier": re.compile(r"\b(?:libpgrazor[\w.-]*|pgrazor_[a-zA-Z0-9_]+)\b"),
    "legacy_path": re.compile(r"\bpgrazor[/\\]"),
    "legacy_brand": re.compile(r"\bPGRazor\b"),
}
TEXT_SUFFIXES = {".py", ".java", ".cpp", ".c", ".h", ".hpp", ".xml", ".json",
                 ".yml", ".yaml", ".md", ".txt", ".js", ".jsx", ".cjs", ".sh",
                 ".ps1", ".cmake", ".map", ".properties", ".gradle", ".svg"}
EXCLUDED_PARTS = {"vendor", "node_modules", "build", "input", ".artifacts"}
HISTORY = {"LICENSE", "THIRD_PARTY.md", "CHANGELOG.md", "docs/NATIVE_MIGRATION.md"}


def tracked_paths(root):
    data = subprocess.check_output(["git", "ls-files", "-z"], cwd=root)
    return [Path(name.decode("utf-8", errors="surrogateescape"))
            for name in data.split(b"\0") if name]


def classify(path):
    name = path.as_posix()
    if name in HISTORY or (name.startswith("docs/releases/") and
                           path.name not in {"README.md", "TEMPLATE.md", "footer.md"}):
        return "history"
    if any(part in EXCLUDED_PARTS for part in path.parts):
        return "excluded"
    return "active"


def inventory(root, paths):
    rows = []
    totals = {group: {key: 0 for key in RULES} for group in ("active", "history")}
    for path in sorted(paths):
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("Invalid tracked path")
        group = classify(path)
        target = root / path
        if group == "excluded" or target.is_symlink() or not target.is_file():
            continue
        if not target.resolve().is_relative_to(root.resolve()):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {
                "LICENSE", "VERSION", "CMakeLists.txt", "Makefile", ".gitignore"}:
            continue
        if target.stat().st_size > 2_000_000:
            continue
        text = target.read_text(encoding="utf-8", errors="replace")
        counts = {key: len(rule.findall(text)) for key, rule in RULES.items()}
        if any(counts.values()):
            rows.append({"path": path.as_posix(), "group": group, "counts": counts})
            for key, count in counts.items():
                totals[group][key] += count
    return {"totals": totals, "files": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Include per-file counts")
    args = parser.parse_args()
    result = inventory(ROOT, tracked_paths(ROOT))
    print(json.dumps(result if args.json else {
        "totals": result["totals"],
        "files_with_matches": len(result["files"]),
    }, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
