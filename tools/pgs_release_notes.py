"""Render reviewed English and Brazilian Portuguese release notes without publishing."""
import argparse
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

def render(version, root=ROOT):
    if not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", version):
        raise ValueError("Expected vX.Y.Z")
    blocks = []
    for folder in ("docs/releases", "docs/pt-BR/releases"):
        text = (root / folder / (version + ".md")).read_text(encoding="utf-8").strip()
        if text.splitlines()[0] != "# PGS " + version:
            raise ValueError("Mismatched release heading: " + folder)
        if re.search(r"\b(?:vVERSION|VERSION_CODE|APK_NAME|APK_SHA256|VERSION)\b", text):
            raise ValueError("Unfilled release template: " + folder)
        blocks.append(text)
    footer = (root / "docs/releases/footer.md").read_text(encoding="utf-8").strip()
    return blocks[0] + "\n\n---\n\n**Português (Brasil)**\n\n" + blocks[1] + "\n\n" + footer + "\n"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    notes = render(args.version)
    if args.output:
        args.output.write_text(notes, encoding="utf-8")
    else:
        print(notes, end="")
