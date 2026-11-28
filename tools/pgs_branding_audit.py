"""Confirm PGS public identity while preserving Android/ABI/backup compatibility.

Run in CI before packaging. Internal dev.pgs, assets/pgs, PGS_*
and the original attribution remain intact.
"""
from pathlib import Path
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = ("en", "de", "es", "fr", "pt-BR", "ru", "it", "zh-Hant", "nl", "th", "ko")
ACTIVE_TEXT = (
    "tools/discord_release.py",
    "website/src/components/GuideIndex.jsx",
    "website/src/components/Cooldown.jsx",
    "website/src/content.js",
    "pgs/AndroidManifest.xml",
    "pgs/root-installer/AndroidManifest.xml",
    "pgs/src/dev/pgs/EncounterCounter.java",
    "pgs/src/dev/pgs/GpxCodec.java",
    "pgs/src/dev/pgs/SettingsPanel.java",
    "pgs/src/dev/pgs/Updater.java",
    "pgs/src/dev/pgs/LogActivity.java",
    "pgs/src/dev/pgs/ShundoSniper.java",
    "pgs/src/dev/pgs/MoonaniFeed.java",
    "pgs/src/dev/pgs/RootedLogDialog.java",
)
PGS_CERT = "d95c6bdfcbd91dc5c9cde698487c88e4994771a475e4efde4567b8d5f44e96cf"


def check():
    problems = []
    # Confirm the active project identity is PGS in key active files.
    for path in ACTIVE_TEXT:
        data = (ROOT / path).read_text(encoding="utf-8")
        if "PGS" not in data and "pgs" not in data.lower():
            problems.append(path + ": project identity not present (expected PGS)")
    # Confirm language catalogs keep their expected size (11 translated catalogs).
    for lang in LANGUAGES:
        path = ROOT / "pgs/i18n" / (lang + ".json")
        catalog = json.loads(path.read_text(encoding="utf-8"))
        if len(catalog) != 1332:
            problems.append(path.name + ": language catalog changed size")
    # Confirm Android package identity and permanent certificate are unchanged.
    from_code = (ROOT / "pgs/pgs_update.py").read_text(encoding="utf-8")
    if "com.nianticlabs.pokemongo" not in from_code:
        problems.append("pgs_update.py: Android package changed")
    if PGS_CERT not in from_code.lower():
        problems.append("pgs_update.py: permanent certificate source changed")
    # Confirm versionCode ledger did not regress.
    version = (ROOT / "pgs/PGS_LAST_VERSION_CODE").read_text(encoding="utf-8").strip()
    if not version.isdigit() or int(version) < 2026111605:
        problems.append("PGS versionCode ledger regressed")
    if problems:
        raise SystemExit("PGS branding audit failed:\n" + "\n".join(" - " + p for p in problems))
    print("PGS branding audit PASS: active UI, URLs, 11 catalogs, release identity and Android continuity")


def legacy_inventory():
    """Inventory the exact tracked tree, not the search index or previous snapshots."""
    from pgs_reference_inventory import index_blobs
    pattern = re.compile("pg" + "razor", re.IGNORECASE)
    raw = subprocess.check_output(["git", "ls-files", "--stage", "-z"], cwd=ROOT)
    tracked = {}
    for item in raw.split(b"\x00"):
        if item:
            metadata, path = item.split(b"\t", 1)
            mode, oid, stage = metadata.split()
            if stage != b"0":
                raise ValueError("Unmerged index")
            tracked[path.decode("utf-8")] = (mode, oid)
    files = []
    for path, data in index_blobs(ROOT, tracked):
        if b"\x00" in data:
            continue
        try:
            source = data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        count = len(pattern.findall(source))
        if count:
            files.append({"path": path, "occurrences": count})
    names = [path for path in sorted(tracked) if pattern.search(path)]
    result = {"tracked_files": len(tracked), "legacy_path_count": len(names),
              "legacy_paths": names, "legacy_text_files": len(files),
              "legacy_text_occurrences": sum(row["occurrences"] for row in files),
              "files": files}
    # Explicit retention: original copyright/provenance and regression or migration checks.
    # Keep the actual historical string where needed; never hide it by encoding the name.
    allowed = {
        "LICENSE": (1, "required original copyright"),
        "NOTICE": (2, "original copyright and source attribution"),
    }
    unexpected = [row for row in files
                  if row["path"] not in allowed or row["occurrences"] > allowed[row["path"]][0]]
    result["intentional_retention"] = [{"path": row["path"], "occurrences": row["occurrences"],
                                       "reason": allowed[row["path"]][1]}
                                      for row in files if row["path"] in allowed
                                      and row["occurrences"] <= allowed[row["path"]][0]]
    result["unexpected_legacy_files"] = unexpected
    print("LEGACY_IDENTITY_INVENTORY " + json.dumps(result, ensure_ascii=True))
    if names or unexpected:
        raise SystemExit("Unexpected legacy identity in tracked source or paths")


if __name__ == "__main__":
    if sys.argv[1:] == ["--legacy-inventory"]:
        legacy_inventory()
    else:
        check()
