"""Offline checks for the authorized same-repository draft input contract."""
import hashlib
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import pgs_pinned_input as pinned


class PgsPinnedInputTests(unittest.TestCase):
    data = b"synthetic test archive"
    profile = {"game_version": "0.439.0", "input_sha256": hashlib.sha256(data).hexdigest()}

    def setUp(self):
        self.size = patch.dict(pinned.EXPECTED_BYTES, {"0.439.0": len(self.data)})
        self.size.start()
        self.addCleanup(self.size.stop)

    def pages(self, draft=True, **overrides):
        asset = {"name": "Pokemon_GO_0.439.0_ARM64_ORIGINAL.apkm", "id": 123,
                 "state": "uploaded", "size": len(self.data),
                 "digest": "sha256:" + self.profile["input_sha256"]}
        asset.update(overrides)
        return [[{"tag_name": "build-inputs", "draft": draft, "assets": [asset]}]]

    def test_exact_draft_and_asset(self):
        self.assertEqual(pinned.resolve_asset([[], *self.pages()], self.profile), 123)

    def test_reject_published_missing_or_duplicate_draft(self):
        for pages in (self.pages(draft=False), [[]], self.pages() + self.pages()):
            with self.subTest(pages=pages), self.assertRaises(ValueError):
                pinned.resolve_asset(pages, self.profile)

    def test_reject_missing_or_duplicate_asset(self):
        for assets in ([], self.pages()[0][0]["assets"] * 2):
            with self.subTest(assets=assets), self.assertRaises(ValueError):
                pinned.resolve_asset([[{"tag_name": "build-inputs", "draft": True, "assets": assets}]],
                                     self.profile)

    def test_reject_incorrect_asset_metadata(self):
        for overrides in ({"name": "wrong.apkm"}, {"state": "open"}, {"size": 1},
                          {"digest": "sha256:" + "0" * 64}, {"id": True}, {"id": 0}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                pinned.resolve_asset(self.pages(**overrides), self.profile)

    def test_reject_unreviewed_profile(self):
        with self.assertRaises(ValueError):
            pinned.expected_asset(dict(self.profile, game_version="0.999.0"))

    def test_download_verifies_hash_and_rechecks_draft(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(pinned, "lookup", return_value=123) as lookup:
            folder = Path(temp)
            def download(*args, **kwargs):
                kwargs["stdout"].write(self.data)
                return SimpleNamespace(returncode=0)
            with patch.object(pinned.subprocess, "run", side_effect=download):
                result = pinned.fetch_archive("gh", {}, self.profile, folder)
            self.assertEqual(result["sha256"], self.profile["input_sha256"])
            self.assertEqual(lookup.call_count, 2)
            self.assertEqual(list(folder.iterdir()), [folder / "game.apkm"])
            self.assertEqual((folder / "game.apkm").read_bytes(), self.data)

    def test_bad_archive_and_changed_asset_leave_no_input(self):
        for bad_hash in (True, False):
            with self.subTest(bad_hash=bad_hash), tempfile.TemporaryDirectory() as temp:
                folder = Path(temp)
                def download(*args, **kwargs):
                    kwargs["stdout"].write(b"x" * len(self.data) if bad_hash else self.data)
                    return SimpleNamespace(returncode=0)
                with patch.object(pinned, "lookup", side_effect=[123, 124]), patch.object(
                        pinned.subprocess, "run", side_effect=download):
                    with self.assertRaises(ValueError):
                        pinned.fetch_archive("gh", {}, self.profile, folder)
                self.assertEqual(list(folder.iterdir()), [])

    def test_stale_input_rejected_without_network(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(pinned, "lookup") as lookup:
            folder = Path(temp)
            (folder / "game.apkm").write_bytes(b"existing")
            with self.assertRaises(ValueError):
                pinned.fetch_archive("gh", {}, self.profile, folder)
            lookup.assert_not_called()
            self.assertEqual((folder / "game.apkm").read_bytes(), b"existing")

    def test_signer_not_loaded_without_verified_input(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(pinned, "required_setting") as setting:
            folder = Path(temp)
            with self.assertRaises(ValueError):
                pinned.load_key(self.profile, folder)
            setting.assert_not_called()

    def test_download_environment_excludes_signing_material(self):
        with patch.dict(os.environ, {"GH_TOKEN": "synthetic", "GITHUB_REPOSITORY": pinned.REPOSITORY,
                                    "PGS_KEYSTORE_BASE64": "test-key", "PGS_STORE_PASSWORD": "test-password"},
                        clear=True), patch.object(pinned.shutil, "which", return_value="gh"):
            _, env = pinned.github_env()
            self.assertEqual(env["GH_TOKEN"], "synthetic")
            self.assertNotIn("PGS_KEYSTORE_BASE64", env)
            self.assertNotIn("PGS_STORE_PASSWORD", env)


if __name__ == "__main__":
    unittest.main()
