"""PGS Discord releases must never link or announce upstream APK assets."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import discord_release


TAG = "v0.0.1"
RELEASE = "https://github.com/LucianoToscano/PGS/releases/"
BASE = RELEASE + "download/" + TAG + "/"
APK = {"name": "PGS.v0.0.1.apk", "size": 185_000_000,
       "browser_download_url": BASE + "PGS.v0.0.1.apk"}
SUMS = {"name": "SHA256SUMS.txt",
        "browser_download_url": BASE + "SHA256SUMS.txt"}
HIGHLIGHT = {"name": "release-highlight.png",
             "browser_download_url": BASE + "release-highlight.png"}


def release(assets, **extra):
    r = {"tag_name": TAG, "name": "PGS v0.0.1",
         "html_url": RELEASE + "tag/" + TAG,
         "body": "Independent PGS release.", "assets": assets}
    r.update(extra)
    return r


class DiscordReleaseTests(unittest.TestCase):
    def test_complete_pgs_release_only(self):
        payload = discord_release.message(release([APK, SUMS]))
        self.assertEqual(payload["username"], "PGS Releases")
        self.assertEqual(payload["embeds"][0]["footer"]["text"], "PGS | Release")
        self.assertTrue(any(APK["browser_download_url"] in f["value"]
                            for f in payload["embeds"][0]["fields"]))
        self.assertNotIn("ko-fi.com", str(payload))

    def test_optional_highlight(self):
        payload = discord_release.message(release([APK, SUMS, HIGHLIGHT]))
        self.assertEqual(payload["embeds"][0]["image"]["url"], HIGHLIGHT["browser_download_url"])
        self.assertNotIn("image", discord_release.message(release([APK, SUMS]))["embeds"][0])

    def test_role_ping_is_opt_in(self):
        role = "123456789012345678"
        self.assertNotIn("content", discord_release.message(release([APK, SUMS])))
        payload = discord_release.message(release([APK, SUMS]), role)
        self.assertEqual(payload["content"], "<@&" + role + "> A new PGS release is available!")
        self.assertEqual(payload["allowed_mentions"]["roles"], [role])
        self.assertEqual(payload["allowed_mentions"]["parse"], [])

    def test_reject_incomplete_or_foreign_release(self):
        cases = [
            release([APK]), release([SUMS]),
            release([dict(APK, size=200_000), SUMS]),
            release([dict(APK, name="PGS.apk"), SUMS]),
            release([dict(APK, browser_download_url="https://example.com/PGS.v0.0.1.apk"), SUMS]),
            release([APK, SUMS], draft=True),
            release([APK, SUMS], tag_name="v0.3.8-pgs.3"),
            release([APK, SUMS], html_url="https://github.com/jpitty03/PGS/releases/tag/v0.0.1"),
        ]
        for case in cases:
            with self.subTest(case=case), self.assertRaises(ValueError):
                discord_release.message(case)


if __name__ == "__main__":
    unittest.main()
