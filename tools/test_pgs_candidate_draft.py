"""Offline checks for the opt-in candidate retention boundary."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pgs_candidate_draft as draft
from pgs_build_request import BuildRequest


class CandidateDraftTests(unittest.TestCase):
    commit = "a" * 40
    request = BuildRequest("v0.0.5", "v0.0.4", 2026111607, 2026111608, "d" * 64, True)
    profile = {"game_version": "0.439.0", "version_code": 2026111602, "input_sha256": "b" * 64}

    def fixture(self, source):
        apk = source / "PGS.apk"
        apk.write_bytes(b"synthetic candidate test data")
        sha = draft.digest(apk)
        receipt = {"status": "STATIC_CANDIDATE_CHECKS_PASSED", "release_asset": self.request.asset,
                   "bytes": apk.stat().st_size, "sha256": sha, "version_code": self.request.previous_code + 1,
                   "device_tested": False, "in_place_update_tested": False, "publish_ready": False}
        info = {"source_commit": self.commit, "device_tested": False, "game_version": self.profile["game_version"],
                "game_version_code": self.profile["version_code"], "input_sha256": self.profile["input_sha256"],
                "apk_version_code": receipt["version_code"], "apk_sha256": sha}
        (source / "PGS.json").write_text(json.dumps(receipt), encoding="utf-8")
        (source / "build-info.json").write_text(json.dumps(info), encoding="utf-8")
        (source / "SHA256SUMS.txt").write_text(sha + "  PGS.apk\n", encoding="utf-8")
        return receipt

    def test_candidate_allocation(self):
        self.assertEqual(self.request.tag, "v0.0.5")
        self.assertEqual(self.request.previous_code, 2026111607)
        self.assertEqual(self.request.asset, "PGS.v0.0.5.apk")

    def test_authorization_requires_exact_request_and_main_context(self):
        valid = {"PGS_RETAIN_AUTHORIZED": "true", "GITHUB_REPOSITORY": draft.REPOSITORY,
                 "GITHUB_EVENT_NAME": "push", "GITHUB_REF": "refs/heads/main",
                 "GITHUB_SHA": self.commit, "PGS_VERSION": self.request.tag,
                 "PGS_EXPECTED_VERSION_CODE": str(self.request.expected_code)}
        self.assertEqual(draft.authorized_commit(valid, self.request), self.commit)
        for key in valid:
            with self.subTest(key=key), self.assertRaises(ValueError):
                draft.authorized_commit(dict(valid, **{key: "invalid"}), self.request)
        manual = dict(valid, GITHUB_EVENT_NAME="workflow_dispatch",
                      PGS_MANUAL_AUTHORIZED="true", PGS_MANUAL_RETAIN="true")
        self.assertEqual(draft.authorized_commit(manual, self.request), self.commit)
        with self.assertRaises(ValueError):
            draft.authorized_commit(dict(manual, PGS_MANUAL_RETAIN="false"), self.request)

    def test_refuses_existing_release_or_tag(self):
        with patch.object(draft, "releases", return_value=[{"tag_name": self.request.tag, "draft": True}]):
            with self.assertRaises(ValueError):
                draft.require_unused_target("gh", {}, self.request)
        with patch.object(draft, "releases", return_value=[]), patch.object(
                draft, "run_gh", return_value=json.dumps([{"ref": "refs/tags/" + self.request.tag}])):
            with self.assertRaises(ValueError):
                draft.require_unused_target("gh", {}, self.request)

    def test_previous_signed_candidate_is_bound_to_receipt_and_digest(self):
        request = self.request
        apk = {"name": "PGS." + request.previous_tag + ".apk", "id": 1,
               "state": "uploaded", "size": 185000000,
               "digest": "sha256:" + request.previous_apk_sha256}
        receipt_asset = {"name": "PGS.json", "id": 2, "state": "uploaded", "size": 1000}
        rows = [{"tag_name": request.previous_tag, "assets": [apk, receipt_asset]}]
        receipt = {"pgs_version": request.previous_tag, "release_asset": apk["name"],
                   "version_code": request.previous_code, "sha256": request.previous_apk_sha256,
                   "bytes": apk["size"], "signing_certificate_sha256": draft.SIGNER}
        with patch.object(draft, "releases", return_value=rows), patch.object(
                draft, "run_gh", return_value=json.dumps(receipt)):
            draft.require_previous_candidate("gh", {}, request)
        for changed in ({"version_code": request.previous_code - 1}, {"sha256": "wrong"},
                        {"signing_certificate_sha256": "other"}):
            with patch.object(draft, "releases", return_value=rows), patch.object(
                    draft, "run_gh", return_value=json.dumps(dict(receipt, **changed))):
                with self.assertRaises(ValueError):
                    draft.require_previous_candidate("gh", {}, request)

    def test_stage_only_canonical_four_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, target = Path(tmp) / "source", Path(tmp) / "target"
            source.mkdir()
            target.mkdir()
            receipt = self.fixture(source)
            (source / "game.apkm").write_bytes(b"not for retention")
            (source / "key.jks").write_bytes(b"not for retention")
            expected = draft.stage_bundle(source, target, self.profile, self.commit, lambda *a, **k: receipt, self.request)
            self.assertEqual(set(expected), set(self.request.names))
            self.assertEqual({p.name for p in target.iterdir()}, set(self.request.names))
            self.assertEqual((target / "SHA256SUMS.txt").read_text(encoding="utf-8").split(),
                             [receipt["sha256"], self.request.asset])

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
                    draft.stage_bundle(source, target, self.profile, self.commit, lambda *a, **k: receipt, self.request)
                self.assertEqual(list(target.iterdir()), [])

    def test_verify_retained_draft_requires_exact_assets_and_source(self):
        expected = {name: {"size": 10, "digest": "sha256:" + "c" * 64} for name in self.request.names}
        assets = [dict(meta, name=name, state="uploaded") for name, meta in expected.items()]
        row = {"tag_name": self.request.tag, "draft": True, "target_commitish": self.commit, "assets": assets}
        draft.verify_retained([row], expected, self.commit, self.request)
        for override in ({"draft": False}, {"target_commitish": "wrong"}, {"assets": assets[:-1]},
                         {"assets": [dict(assets[0], digest="wrong"), *assets[1:]]}):
            with self.subTest(override=override), self.assertRaises(ValueError):
                draft.verify_retained([dict(row, **override)], expected, self.commit, self.request)

    def test_retention_command_is_draft_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            source.mkdir()
            receipt = self.fixture(source)
            with patch.object(draft, "require_unused_target") as unused, patch.object(
                    draft, "run_gh", return_value="") as gh, patch.object(
                    draft, "releases", return_value=[]) as releases, patch.object(draft, "verify_retained") as verify:
                draft.retain("gh", {}, source, self.profile, self.commit, lambda *a, **k: receipt, self.request)
            args = gh.call_args.args[2]
            self.assertEqual(args[:3], ["release", "create", self.request.tag])
            self.assertIn("--draft", args)
            self.assertIn(self.commit, args)
            self.assertEqual({Path(p).name for p in args[-4:]}, set(self.request.names))
            self.assertNotIn("--clobber", args)
            self.assertEqual(unused.call_count, 2)
            releases.assert_called_once()
            verify.assert_called_once()


if __name__ == "__main__":
    unittest.main()
