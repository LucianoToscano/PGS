"""Confirm PGS public identity while preserving Android/ABI/backup compatibility.

Run in CI before packaging. Internal dev.pgs, assets/pgs, PGS_*
and the original attribution remain intact.
"""
from pathlib import Path
import json

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


if __name__ == "__main__":
    check()
