"""Read the original project name from the repository attribution."""
from pathlib import Path


def upstream_name():
    notice = Path(__file__).resolve().parents[1] / "NOTICE"
    for line in notice.read_text(encoding="utf-8").splitlines():
        if line.startswith("Original source: "):
            return line.rstrip("/").rsplit("/", 1)[-1]
    raise ValueError("Missing original source in NOTICE")
