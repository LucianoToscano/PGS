"""Guard PGS public identity while preserving Android/ABI/backup compatibility.

Run in CI before packaging. Internal dev.pgrazor, assets/pgrazor, PGRAZOR_*
and the original attribution remain intact until migrated with proofs.
"""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = ("en", "de", "es", "fr", "pt-BR", "ru", "it", "zh-Hant", "nl", "th", "ko")
ACTIVE_TEXT = (
    "tools/discord_release.py",
    "website/src/components/GuideIndex.jsx",
    "website/src/components/Cooldown.jsx",
    "website/src/content.js",
    "pgrazor/AndroidManifest.xml",
    "pgrazor/root-installer/AndroidManifest.xml",
    "pgrazor/src/dev/pgrazor/EncounterCounter.java",
    "pgrazor/src/dev/pgrazor/GpxCodec.java",
    "pgrazor/src/dev/pgrazor/SettingsPanel.java",
    "pgrazor/src/dev/pgrazor/Updater.java",
    "pgrazor/src/dev/pgrazor/LogActivity.java",
    "pgrazor/src/dev/pgrazor/ShundoSniper.java",
    "pgrazor/src/dev/pgrazor/MoonaniFeed.java",
    "pgrazor/src/dev/pgrazor/RootedLogDialog.java",
)
PGS_REPO = "https://github.com/LucianoToscano/PGS"
PGS_CERT = "d95c6bdfcbd91dc5c9cde698487c88e4994771a475e4efde4567b8d5f44e96cf"


def check():
    problems = []
    for path in ACTIVE_TEXT:
        data = (ROOT / path).read_text(encoding="utf-8")
        if "PGRazor" in data:
            problems.append(path + ": legacy brand appears in active content")
        if "https://discord.gg/9QqfkDSQX3" in data:
            problems.append(path + ": old Discord invitation")
        if "https://github.com/jpitty03/PGRazor/releases/download/" in data:
            problems.append(path + ": upstream APK download")
    for lang in LANGUAGES:
        path = ROOT / "pgrazor/i18n" / (lang + ".json")
        catalog = json.loads(path.read_text(encoding="utf-8"))
        if len(catalog) != 1332:
            problems.append(path.name + ": language catalog changed size")
        if any("PGRazor" in key or "PGRazor" in value for key, value in catalog.items()):
            problems.append(path.name + ": untranslated public brand")
    docs = ROOT / "docs/releases"
    for file in docs.glob("*.md"):
        if "https://github.com/jpitty03/PGRazor/releases/download/" in file.read_text(encoding="utf-8"):
            problems.append(str(file.relative_to(ROOT)) + ": upstream APK link")
    for path in ("website/package.json", "website/package-lock.json"):
        if "pgrazor-website" in (ROOT / path).read_text(encoding="utf-8"):
            problems.append(path + ": old package name")
    funding = (ROOT / ".github/FUNDING.yml").read_text(encoding="utf-8")
    if re.search(r"(?im)^\s*ko_fi\s*:\s*pgrazor\b", funding):
        problems.append("FUNDING.yml: donations still point to upstream account")
    if "PGRazor.apk" in (ROOT / "pgrazor/release_apk.py").read_text(encoding="utf-8"):
        problems.append("release_apk.py: can still emit an upstream-named APK")
    release = (ROOT / "tools/discord_release.py").read_text(encoding="utf-8")
    if "PGS." not in release or "SHA256SUMS.txt" not in release:
        problems.append("Discord release announcement not restricted to verified PGS APK")
    flow = (ROOT / ".github/workflows/discord-release.yml").read_text(encoding="utf-8")
    if "secrets.PGS_DISCORD_RELEASE_WEBHOOK" not in flow or "vars.PGS_DISCORD_CHANNEL_ID" not in flow:
        problems.append("Discord release workflow does not require PGS-specific configuration")
    from_code = (ROOT / "pgrazor/pgs_update.py").read_text(encoding="utf-8")
    if "com.nianticlabs.pokemongo" not in from_code or PGS_CERT not in from_code.lower():
        problems.append("PGS package or permanent certificate source changed")
    version = (ROOT / "pgrazor/PGS_LAST_VERSION_CODE").read_text(encoding="utf-8").strip()
    if not version.isdigit() or int(version) < 2026111605:
        problems.append("PGS versionCode ledger regressed")
    if problems:
        raise SystemExit("PGS branding audit failed:\n" + "\n".join(" - " + p for p in problems))
    print("PGS branding audit PASS: active UI, URLs, 11 catalogs, release identity and Android continuity")


if __name__ == "__main__":
    check()
