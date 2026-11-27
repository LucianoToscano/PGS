"""Announce verified published PGS releases only in the configured PGS Discord channel."""
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

REPOSITORY = "LucianoToscano/PGS"
RELEASE_PREFIX = "https://github.com/" + REPOSITORY + "/releases/"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def request(url, *, token=None, payload=None):
    headers = {"User-Agent": "PGS-release-announcer", "Accept": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.build_opener(NoRedirect()).open(req, timeout=30) as response:
        return json.load(response)


def message(release, role_id=""):
    """Pure message builder. Never announce an upstream or incomplete APK."""
    role_id = role_id.strip()
    if role_id and not re.fullmatch(r"[0-9]{17,20}", role_id):
        raise ValueError("PGS_DISCORD_RELEASE_ROLE_ID must be a numeric role ID")
    tag = release.get("tag_name", "")
    if not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", tag):
        raise ValueError("Invalid PGS release tag")
    if release.get("draft"):
        raise ValueError("Draft releases must not be announced")
    url = release.get("html_url", "")
    if url != RELEASE_PREFIX + "tag/" + tag:
        raise ValueError("Release belongs to a different repository")
    assets = release.get("assets") or []
    filename = "PGS." + tag + ".apk"
    download_prefix = RELEASE_PREFIX + "download/" + tag + "/"
    def valid_asset(name):
        return next((item for item in assets
                     if item.get("name") == name
                     and item.get("browser_download_url") == download_prefix + name), None)
    apk = valid_asset(filename)
    checksums = valid_asset("SHA256SUMS.txt")
    if not apk or not checksums or int(apk.get("size", 0)) < 100_000_000:
        raise ValueError("PGS release lacks full APK or checksum asset")
    highlight = valid_asset("release-highlight.png")
    description = (release.get("body") or "See PGS GitHub for release details.").strip()
    if len(description) > 3000:
        description = description[:2997] + "..."
    fields = [
        {"name": "Download", "value": "[Install " + filename + "](" + apk["browser_download_url"] + ")"},
        {"name": "SHA-256", "value": "[Check SHA256SUMS.txt](" + checksums["browser_download_url"] + ")"}
    ]
    kind = "Prerelease" if release.get("prerelease") else "Release"
    embed = {"title": (release.get("name") or "PGS " + tag)[:256],
             "url": url, "description": description, "color": 0x35DAB4,
             "fields": fields, "footer": {"text": "PGS | " + kind}}
    if highlight:
        embed["image"] = {"url": highlight["browser_download_url"]}
    payload = {"username": "PGS Releases", "allowed_mentions": {"parse": []}, "embeds": [embed]}
    if role_id:
        payload["content"] = "<@&" + role_id + "> A new PGS release is available!"
        payload["allowed_mentions"]["roles"] = [role_id]
    return payload


def main():
    webhook = os.environ.get("PGS_DISCORD_RELEASE_WEBHOOK", "").strip()
    channel = os.environ.get("PGS_DISCORD_CHANNEL_ID", "").strip()
    if not webhook or not channel:
        print("::warning::Configure PGS_DISCORD_RELEASE_WEBHOOK and PGS_DISCORD_CHANNEL_ID. No announcement sent.")
        return
    if not re.fullmatch(r"https://discord\.com/api(?:/v[0-9]+)?/webhooks/[0-9]+/[A-Za-z0-9_.-]+", webhook):
        raise ValueError("Invalid PGS Discord webhook URL")
    if not re.fullmatch(r"[0-9]{17,20}", channel):
        raise ValueError("Invalid PGS Discord channel ID")
    repo = os.environ["GITHUB_REPOSITORY"]
    if repo != REPOSITORY:
        raise ValueError("Refusing release from another repository")
    tag = urllib.parse.quote(os.environ["RELEASE_TAG"], safe="")
    release = request("https://api.github.com/repos/" + repo + "/releases/tags/" + tag,
                      token=os.environ["GITHUB_TOKEN"])
    if release.get("draft") or not release.get("published_at"):
        raise ValueError("Only published releases can be announced")
    payload = message(release, os.environ.get("PGS_DISCORD_RELEASE_ROLE_ID", ""))
    hook = request(webhook)
    if str(hook.get("channel_id")) != channel:
        raise ValueError("Webhook belongs to another channel; nothing sent")
    # No automatic retry: a lost response must never duplicate announcements.
    result = request(webhook + "?wait=true", payload=payload)
    if not result.get("id"):
        raise ValueError("PGS Discord did not confirm announcement")
    print("PGS release announcement sent.")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as error:
        print("::error::PGS release announcement failed (HTTP " + str(error.code) + ")")
        sys.exit(1)
    except Exception as error:
        # Network exceptions may contain the webhook token. Never print their text.
        print("::error::PGS release announcement failed (" + type(error).__name__ + ").")
        sys.exit(1)
