"""Offline checks for the opt-in candidate retention boundary."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pgs_candidate_draft as draft


class CandidateDraftTests(unittest.TestCase):
    commit = "a" * 40
    profile = {"game_version": "0.439.0", "version_code": 2026111602, "input_sha256": "b" * 64}

    def fixture(self, source):
        apk = source / "PGS.apk"
        apk.write_bytes(b"synthetic candidate test data")
        sha = draft.digest(apk)
        receipt = {"status": "STATIC_CANDIDATE_CHECKS_PASSED", "release_asset": draft.ASSET,
                   "bytes": apk.stat().st_size, "sha256": sha, "version_code": 2026111606,
                   "device_tested": False, "in_place_update_tested": False, "publish_ready": False}
        info = {"source_commit": self.commit, "device_tested": False, "game_version": self.profile["game_version"],
                "game_version_code": self.profile["version_code"], "input_sha256": self.profile["input_sha256"],
                "apk_version_code": receipt["version_code"], "apk_sha256": sha}
        (source / "PGS.json").write_text(json.dumps(receipt), encoding="utf-8")
        (source / "build-info.json").write_text(json.dumps(info), encoding="utf-8")
        (source / "SHA256SUMS.txt").write_text(sha + "  PGS.apk\n", encoding="utf-8")
        return receipt

    def test_authorization_requires_exact_manual_main_context(self):
        valid = {"PGS_RETAIN_AUTHORIZED": "true", "GITHUB_REPOSITORY": draft.REPOSITORY,
                 "GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_REF": "refs/heads/main",
                 "GITHUB_SHA": self.commit}
        self.assertEqual(draft.authorized_commit(valid), self.commit)
        for key in valid:
            with self.subTest(key=key), self.assertRaises(ValueError):
                draft.authorized_commit(dict(valid, **{key: "invalid"}))

    def test_refuses_existing_release_or_tag(self):
        with patch.object(draft, "releases", return_value=[{"tag_name": draft.TAG, "draft": True}]):
            with self.assertRaises(ValueError):
                draft.require_unused_target("gh", {})
        with patch.object(draft, "releases", return_value=[]), patch.object(
                draft, "run_gh", return_value=json.dumps([{"ref": "refs/tags/" + draft.TAG}])):
            with self.assertRaises(ValueError):
                draft.require_unused_target("gh", {})

    def test_stage_only_canonical_four_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, target = Path(tmp) / "source", Path(tmp) / "target"
            source.mkdir()
            target.mkdir()
            receipt = self.fixture(source)
            (source / "game.apkm").write_bytes(b"not for retention")
            (source / "key.jks").write_bytes(b"not for retention")
            expected = draft.stage_bundle(source, target, self.profile, self.commit, lambda *a, **k: receipt)
            self.assertEqual(set(expected), set(draft.NAMES))
            self.assertEqual({p.name for p in target.iterdir()}, set(draft.NAMES))
            self.assertEqual((target / "SHA256SUMS.txt").read_text(encoding="utf-8").split(),
                             [receipt["sha256"], draft.ASSET])

    def test_tampered_candidate_and_receipt_rejected(self):
        for corrupt in ("apk", "receipt", "source"):
            with self.subTest(corrupt=corrupt), tempfile.TemporaryDirectory() as tmp:
                source, target = Path(tmp) / "source", Path(tmp) / "target"
                source.mkdir()
                target.mkdir()
                receipt = self.fixture(source)
                if corrupt == "apk":
                    (source / "PGS.apk").write_bytes(b"tampered")
                elif corrupt == "receipt":
                    (source / "PGS.json").write_text(json.dumps(dict(receipt, publish_ready=True)), encoding="utf-8")
                else:
                    info = json.loads((source / "build-info.json").read_text(encoding="utf-8"))
                    info["source_commit"] = "wrong"
                    (source / "build-info.json").write_text(json.dumps(info), encoding="utf-8")
                with self.assertRaises(ValueError):
                    draft.stage_bundle(source, target, self.profile, self.commit, lambda *a, **k: receipt)
                self.assertEqual(list(target.iterdir()), [])

    def test_verify_retained_draft_requires_exact_assets_and_source(self):
        expected = {name: {"size": 10, "digest": "sha256:" + "c" * 64} for name in draft.NAMES}
        assets = [dict(meta, name=name, state="uploaded") for name, meta in expected.items()]
        row = {"tag_name": draft.TAG, "draft": True, "target_commitish": self.commit, "assets": assets}
        draft.verify_retained([row], expected, self.commit)
        for override in ({"draft": False}, {"target_commitish": "wrong"}, {"assets": assets[:-1]},
                         {"assets": [dict(assets[0], digest="wrong"), *assets[1:]]}):
            with self.subTest(override=override), self.assertRaises(ValueError):
                draft.verify_retained([dict(row, **override)], expected, self.commit)

    def test_retention_command_is_draft_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            source.mkdir()
            receipt = self.fixture(source)
            with patch.object(draft, "require_unused_target") as unused, patch.object(
                    draft, "run_gh", return_value="") as gh, patch.object(
                    draft, "releases", return_value=[]) as releases, patch.object(draft, "verify_retained") as verify:
                draft.retain("gh", {}, source, self.profile, self.commit, lambda *a, **k: receipt)
            args = gh.call_args.args[2]
            self.assertEqual(args[:3], ["release", "create", draft.TAG])
            self.assertIn("--draft", args)
            self.assertIn(self.commit, args)
            self.assertEqual({Path(p).name for p in args[-4:]}, set(draft.NAMES))
            self.assertNotIn("--clobber", args)
            self.assertEqual(unused.call_count, 2)
            releases.assert_called_once()
            verify.assert_called_once()


if __name__ == "__main__":
    unittest.main()
