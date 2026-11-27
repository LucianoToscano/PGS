"""Guard PGS public identity while preserving Android/ABI/backup compatibility.

Run in CI before packaging. Preserve the original attribution, legacy storage
identities and explicitly retained ABI/environment aliases.
"""
from pathlib import Path
import json
import re
import hashlib
import struct

ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = ("en", "de", "es", "fr", "pt-BR", "ru", "it", "zh-Hant", "nl", "th", "ko")
ACTIVE_TEXT = (
    "tools/discord_release.py",
    "website/src/components/GuideIndex.jsx",
    "website/src/components/Cooldown.jsx",
    "website/src/content.js",
    "website/src/content.en.js",
    "website/src/content.pt-BR.js",
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
        path = ROOT / "pgs/i18n" / (lang + ".json")
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
    if "PGRazor.apk" in (ROOT / "pgs/release_apk.py").read_text(encoding="utf-8"):
        problems.append("release_apk.py: can still emit an upstream-named APK")
    release = (ROOT / "tools/discord_release.py").read_text(encoding="utf-8")
    if "PGS." not in release or "SHA256SUMS.txt" not in release:
        problems.append("Discord release announcement not restricted to verified PGS APK")
    flow = (ROOT / ".github/workflows/discord-release.yml").read_text(encoding="utf-8")
    if "secrets.PGS_DISCORD_RELEASE_WEBHOOK" not in flow or "vars.PGS_DISCORD_CHANNEL_ID" not in flow:
        problems.append("Discord release workflow does not require PGS-specific configuration")
    from_code = (ROOT / "pgs/pgs_update.py").read_text(encoding="utf-8")
    if "com.nianticlabs.pokemongo" not in from_code or PGS_CERT not in from_code.lower():
        problems.append("PGS package or permanent certificate source changed")
    version = (ROOT / "pgs/PGS_LAST_VERSION_CODE").read_text(encoding="utf-8").strip()
    if not version.isdigit() or int(version) < 2026111605:
        problems.append("PGS versionCode ledger regressed")
    # Only the exact requested attribution block may use the upstream
    # public name in README. Internal ABI and saved-state identifiers are
    # checked by their own compatibility fixtures rather than renamed here.
    required_license = (
        "Original PGRazor source is available under the MIT License. "
        + "Third-party components retain their own licenses. "
        + "Pokémon GO and its assets are not covered by this license. "
        + "PGRazor is an independent project and is not affiliated with the game publisher."
    )
    for readme_file in ("README.md", "README.pt-BR.md"):
        readme = (ROOT / readme_file).read_text(encoding="utf-8").rstrip()
        if not readme.endswith(required_license):
            problems.append(readme_file + ": mandatory exact final License notice absent")
        elif "pgrazor" in readme[:-len(required_license)].lower():
            problems.append(readme_file + ": legacy brand occurs outside the retained attribution")
        license_section = readme.rsplit("\n## License\n", 1)
        if len(license_section) != 2 or not all(link in license_section[1] for link in ("(LICENSE)", "(NOTICE)", "(THIRD_PARTY_LICENSES.md)")):
            problems.append(readme_file + ": project license and attribution links missing")
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    if not all(line in license_text.splitlines() for line in ("Copyright (c) 2026 PGS contributors", "Copyright (c) 2026 PGRazor contributors")):
        problems.append("LICENSE: project or upstream copyright missing")
    for name in ("NOTICE", "THIRD_PARTY_LICENSES.md"):
        if not (ROOT / name).is_file():
            problems.append(name + ": required attribution document missing")
    # The public GitHub home is bilingual and uses the exact requested stacked title.
    stacked_title = '<h1 align="center">PGS</h1>' + chr(10) + '<h3 align="center">Pokémon GO Spoofers</h3>'
    for readme_file in ("README.md", "README.pt-BR.md"):
        content = (ROOT / readme_file).read_text(encoding="utf-8")
        if stacked_title not in content:
            problems.append(readme_file + ": PGS title must be centered above the subtitle")
        if "PGS — Pokémon GO Spoofers</h1>" in content:
            problems.append(readme_file + ": obsolete single-line heading reintroduced")
        if "docs/en/PGS_REPOSITORY_SETTINGS.md" not in content or "docs/pt-BR/PGS_REPOSITORY_SETTINGS.md" not in content:
            problems.append(readme_file + ": bilingual repository settings link missing")
    for lang in ("en", "pt-BR"):
        if not (ROOT / "docs" / lang / "PGS_REPOSITORY_SETTINGS.md").is_file():
            problems.append("Missing bilingual repository settings guide: " + lang)
    if "id: 'pgs-root'" not in (ROOT / "website/src/featureGuides.js").read_text(encoding="utf-8"):
        problems.append("The Root guide must use a PGS-specific public id")
    if "'pgs-root': {" not in (ROOT / "website/src/featureGuides.pt-BR.d.js").read_text(encoding="utf-8"):
        problems.append("The PGS Root Portuguese guide translation is missing")
    if "guide === 'pgrazor-root' ? 'pgs-root'" not in (ROOT / "website/src/App.jsx").read_text(encoding="utf-8"):
        problems.append("Older Root guide bookmarks must still resolve")
    if "PGRazor" in (ROOT / "pgs/root-installer/src/dev/pgs/root/RootStatus.java").read_text(encoding="utf-8"):
        problems.append("Root status still displays the old name")
    pages = (ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8")
    if "name: Website" not in pages or "workflow_dispatch:" not in pages:
        problems.append("Website workflow must remain discoverable and manually runnable")
    required_pairs = (
        ("README.md", "README.pt-BR.md"),
        ("CHANGELOG.md", "CHANGELOG.pt-BR.md"),
        ("CONTRIBUTING.md", "CONTRIBUTING.pt-BR.md"),
    )
    for english, portuguese in required_pairs:
        en_text = (ROOT / english).read_text(encoding="utf-8")
        pt_text = (ROOT / portuguese).read_text(encoding="utf-8")
        if portuguese not in en_text or english not in pt_text:
            problems.append(english + " / " + portuguese + ": bilingual links missing")
        if "v0.0.2" not in en_text or "v0.0.2" not in pt_text:
            if english != "CONTRIBUTING.md":
                problems.append(english + " / " + portuguese + ": release version mismatch")
    for guide in ("BUILDING.md", "PGS_UPDATE_POLICY.md", "PGS_LANGUAGES.md"):
        for language in ("en", "pt-BR"):
            path = ROOT / "docs" / language / guide
            if not path.is_file():
                problems.append(str(path.relative_to(ROOT)) + ": translated guide missing")
    for public_file in (
        "CONTRIBUTING.md",
        "CHANGELOG.md",
        "CHANGELOG.pt-BR.md",
        "CONTRIBUTING.pt-BR.md",
        "docs/BUILDING.md",
        "docs/ROOTED.md",
        "docs/ARCHITECTURE.md",
        "docs/releases/v0.0.2.md",
        "website/README.md",
        "website/src/content.js",
        "website/src/content.en.js",
        "website/src/content.pt-BR.js",
        "website/src/components/Footer.jsx",
        "website/index.html",
        "website/src/hooks/useTheme.js",
    ):
        content = (ROOT / public_file).read_text(encoding="utf-8")
        if "PGRazor" in content or "https://github.com/jpitty03/PGRazor" in content:
            problems.append(public_file + ": old name remains in public copy")
    # Official graphics are original PNG files, not lossy/redrawn SVG approximations.
    # The same original file bytes are committed for the website and branding sources.
    expected_logos = {
        "pgs-shield.png": (
            "30f51e26c20ea0aba1687e4c1e22adce093b238c3879492342163f818b438300", 4096, 4096
        ),
        "pgs-full.png": (
            "15716009d2d1c0e11d75ace39783c3237c1d9db2272ca7f2fad8ac2d6e20ab2e", 4096, 4096
        ),
        "pgs-wordmark.png": (
            "8ad6e5d80075145154ebfc343d91469da970fa7cfa729b9f6e31479307d4b29e", 4096, 1704
        ),
    }
    for basename, (expected_sha256, expected_width, expected_height) in expected_logos.items():
        for folder in ("website/public", "pgs/branding"):
            path = ROOT / folder / basename
            if not path.is_file():
                problems.append(str(path.relative_to(ROOT)) + ": original PNG missing")
                continue
            content = path.read_bytes()
            if not content.startswith(bytes((137, 80, 78, 71, 13, 10, 26, 10))):
                problems.append(str(path.relative_to(ROOT)) + ": not a PNG")
                continue
            if hashlib.sha256(content).hexdigest() != expected_sha256:
                problems.append(str(path.relative_to(ROOT)) + ": pixels/source bytes differ from Drive original")
            width, height = struct.unpack(">II", content[16:24])
            if (width, height) != (expected_width, expected_height):
                problems.append(str(path.relative_to(ROOT)) + ": resolution regressed")
    for old_logo in (
        "website/public/logo.svg",
        "website/public/pgs-official.svg",
        "pgs/branding/pgs.svg",
        "pgs/branding/pgrazor.svg",
    ):
        if (ROOT / old_logo).exists():
            problems.append(old_logo + ": obsolete traced SVG remains")
    # The legacy screenshot identified another project, and must not be reused
    # as evidence of the current PGS home menu.
    obsolete_menu = ROOT / "website/public/images/main-menu.png"
    if obsolete_menu.exists():
        problems.append("Old main-menu.png screenshot remains published")
    for source in ("README.md", "website/src/content.js", "website/README.md"):
        if "images/main-menu.png" in (ROOT / source).read_text(encoding="utf-8"):
            problems.append(source + ": still advertises the obsolete menu screenshot")
    if "PGSharp" in (ROOT / "README.md").read_text(encoding="utf-8"):
        problems.append("README.md: names another product in PGS public installation guidance")
    public_references = {
        "README.md": "website/public/pgs-full.png",
        "website/index.html": "%BASE_URL%pgs-shield.png",
        "website/src/components/Header.jsx": "asset('pgs-shield.png')",
        "website/src/components/Footer.jsx": "asset('pgs-shield.png')",
        "website/src/components/Hero.jsx": "asset('pgs-wordmark.png')",
    }
    for filename, wanted in public_references.items():
        if wanted not in (ROOT / filename).read_text(encoding="utf-8"):
            problems.append(filename + ": official PGS PNG reference missing")
    for public_file in ("website/index.html", "website/src/hooks/useTheme.js"):
        content = (ROOT / public_file).read_text(encoding="utf-8")
        if "'pgs-theme'" not in content or "'pgrazor-theme'" in content:
            problems.append(public_file + ": website theme identity not PGS")
    # The English catalog owns the canonical download URL; Portuguese shares
    # exactly the same link object and never points at a separate APK.
    for public_file in ("website/src/content.en.js", "website/index.html", "website/tests/site.spec.js"):
        content = (ROOT / public_file).read_text(encoding="utf-8")
        if "/actions/runs/45980315394" not in content:
            problems.append(public_file + ": does not point to the verified PGS v0.0.2 build run")
        if "/actions/workflows/pgs-v0.0.2-release.yml" in content:
            problems.append(public_file + ": download points to a retired rebuild workflow")
    if "export const links = en.links;" not in (ROOT / "website/src/content.pt-BR.js").read_text(encoding="utf-8"):
        problems.append("Brazilian Portuguese catalog must share canonical PGS release links")
    for source_file in (
        "website/src/locale.js",
        "website/src/uiText.js",
        "website/src/featureGuides.i18n.js",
        "website/src/guideScreenshots.i18n.js",
    ):
        if not (ROOT / source_file).is_file():
            problems.append(source_file + ": bilingual website module missing")
    if not (ROOT / ".github/workflows/pgs-v0.0.3-candidate.yml").is_file():
        problems.append("Current full candidate validation workflow missing")
    if problems:
        raise SystemExit("PGS branding audit failed:\n" + "\n".join(" - " + p for p in problems))
    print("PGS branding audit PASS: active UI, URLs, 11 catalogs, release identity and Android continuity")


if __name__ == "__main__":
    check()
