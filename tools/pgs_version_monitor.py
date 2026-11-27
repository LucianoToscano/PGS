"""Read public version metadata only; never fetch APK files."""
import argparse
import os
import re
import sys
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.parse import urlsplit

SOURCE = "https://www.apkmirror.com/uploads/?appcategory=pokemon-go"
VERSION = re.compile(r"^\d+\.\d+\.\d+$")
TITLE = re.compile(r"^Pok[eé]mon\s+GO\s+(\d+\.\d+\.\d+)$", re.I)
MAX_BYTES = 4 * 1024 * 1024


def version_key(value):
    if not VERSION.fullmatch(value):
        raise ValueError("Expected a version in x.y.z format")
    return tuple(map(int, value.split(".")))


class Catalog(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.versions = set()
        self.in_heading = False
        self.buffer = []

    def handle_starttag(self, tag, attrs):
        if tag in ("h2", "h3", "h4", "h5", "h6"):
            self.in_heading = True
            self.buffer = []

    def handle_data(self, data):
        if self.in_heading:
            self.buffer.append(data)

    def handle_endtag(self, tag):
        if tag in ("h2", "h3", "h4", "h5", "h6") and self.in_heading:
            title = " ".join("".join(self.buffer).split())
            match = TITLE.fullmatch(title)
            if match:
                self.versions.add(match.group(1))
            self.in_heading = False
            self.buffer = []


def latest_version(html):
    parser = Catalog()
    parser.feed(html)
    if not parser.versions:
        raise ValueError("No matching stable-version headings; catalog unavailable or format changed")
    return max(parser.versions, key=version_key)


def query():
    request = Request(SOURCE, headers={"User-Agent": "PGS-Version-Monitor/1.0"})
    with urlopen(request, timeout=20) as response:
        target = urlsplit(response.geturl())
        if target.scheme != "https" or target.hostname != "www.apkmirror.com":
            raise ValueError("Unexpected catalog redirect")
        if response.headers.get_content_type() != "text/html":
            raise ValueError("Unexpected catalog response type")
        body = response.read(MAX_BYTES + 1)
        if len(body) > MAX_BYTES:
            raise ValueError("Catalog response exceeds size limit")
        return latest_version(body.decode("utf-8", errors="replace"))


def reviewed_version(profile_version, override=""):
    """Use the reviewed game profile; an optional override may only increase it."""
    version_key(profile_version)
    if not override:
        return profile_version
    return max(profile_version, override, key=version_key)


def new_version(latest, known):
    """Return a newer stable catalog version, or an empty string."""
    if not known:
        return ""
    return latest if version_key(latest) > version_key(known) else ""


def self_test():
    example = """<h5><a>Pokémon GO 0.439.0</a></h5>
    <h5>Pokémon GO 0.99.0</h5><h5>Pokémon GO 9.0.0 beta</h5>
    <h5>Other app 99.0.0</h5>"""
    assert latest_version(example) == "0.439.0"
    assert version_key("0.439.0") > version_key("0.99.0")
    assert new_version("0.440.0", "0.439.0") == "0.440.0"
    assert new_version("0.439.0", "0.439.0") == ""
    assert new_version("0.438.0", "0.439.0") == ""
    assert new_version("0.439.0", "") == ""
    assert reviewed_version("0.439.0") == "0.439.0"
    assert reviewed_version("0.439.0", "0.438.0") == "0.439.0"
    assert reviewed_version("0.439.0", "0.440.0") == "0.440.0"
    try:
        latest_version("<html>Access denied</html>")
    except ValueError:
        pass
    else:
        raise AssertionError("Missing catalog data must fail")
    print("Offline tests passed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    from game_update import current_profile
    known = reviewed_version(current_profile()["game_version"],
                             os.environ.get("PGS_GAME_REVIEWED_VERSION", "").strip())
    latest = query()
    newer = new_version(latest, known)
    status = ("No reviewed version configured" if not known else
              "New catalog version; compatibility not established"
              if newer else
              "No newer catalog version than reviewed version")
    summary = (f"## PGS version monitor\n\n"
               f"- Catalog: {SOURCE}\n"
               f"- Latest observed stable version: {latest}\n"
               f"- Reviewed version: {known or 'not configured'}\n"
               f"- Status: {status}\n"
               "- Metadata only. No APK downloaded, no build or release triggered.\n")
    print(summary)
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as stream:
            stream.write(f"new_version={newer}\n")
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as stream:
            stream.write(summary)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        print(f"Version check failed: {exc}", file=sys.stderr)
        sys.exit(1)
