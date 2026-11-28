"""Offline tests for explicit, monotonic PGS build requests and event gates."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock

import pgs_build_request as build


class BuildRequestTests(unittest.TestCase):
    profile = {"game_version": "0.439.0", "version_code": 2026111602,
               "input_sha256": "a" * 64}
    previous = 2026111607
    data = {"schema": 1, "enabled": True, "version": "v0.0.5",
            "previous_version_code": previous, "previous_apk_sha256": "b" * 64,
            "game_version": profile["game_version"], "game_version_code": profile["version_code"],
            "input_sha256": profile["input_sha256"], "authorized_input": True,
            "retain_authorized_candidate": True}
    env = {"GITHUB_REPOSITORY": build.REPOSITORY, "GITHUB_REF": "refs/heads/main",
           "GITHUB_SHA": "c" * 40, "GITHUB_EVENT_NAME": "push"}

    def parse(self, data):
        return build.parse_request(data, "0.0.4", self.previous, self.profile)

    def test_disabled_and_next_version(self):
        self.assertIsNone(self.parse({"schema": 1, "enabled": False}))
        request = self.parse(self.data)
        self.assertEqual(request.tag, "v0.0.5")
        self.assertEqual(request.previous_tag, "v0.0.4")
        self.assertEqual(request.expected_code, 2026111608)
        self.assertEqual(request.asset, "PGS.v0.0.5.apk")
        self.assertTrue(build.authorize(request, self.env))

    def test_invalid_requests_fail_closed(self):
        for override in ({"enabled": False}, {"schema": True}, {"authorized_input": False},
                         {"retain_authorized_candidate": "true"}, {"version": "v0.0.4"},
                         {"version": "v0.0.6"}, {"previous_version_code": self.previous - 1},
                         {"previous_apk_sha256": "wrong"}, {"game_version": "0.440.0"},
                         {"game_version_code": self.profile["version_code"] + 1},
                         {"input_sha256": "c" * 64}, {"unknown": True}):
            with self.subTest(override=override), self.assertRaises(ValueError):
                self.parse(dict(self.data, **override))

    def test_context_and_manual_retention(self):
        request = self.parse(self.data)
        for override in ({"GITHUB_REPOSITORY": "other/PGS"}, {"GITHUB_REF": "refs/heads/dev"},
                         {"GITHUB_SHA": "bad"}, {"GITHUB_EVENT_NAME": "pull_request"},
                         {"GITHUB_EVENT_NAME": "workflow_dispatch"}):
            with self.subTest(override=override), self.assertRaises(ValueError):
                build.authorize(request, dict(self.env, **override))
        manual = dict(self.env, GITHUB_EVENT_NAME="workflow_dispatch", PGS_MANUAL_AUTHORIZED="true")
        self.assertFalse(build.authorize(request, manual))
        self.assertTrue(build.authorize(request, dict(manual, PGS_MANUAL_RETAIN="true")))
        self.assertFalse(build.authorize(self.parse(dict(self.data, retain_authorized_candidate=False)),
                                         dict(manual, PGS_MANUAL_RETAIN="true")))

    def test_push_requires_changed_request_at_exact_sha(self):
        with tempfile.TemporaryDirectory() as tmp:
            event = Path(tmp) / "event.json"
            event.write_text(json.dumps({"before": "d" * 40, "after": self.env["GITHUB_SHA"]}))
            env = dict(self.env, GITHUB_EVENT_PATH=str(event))
            with patch.object(build.subprocess, "run", return_value=Mock(returncode=1)) as run:
                build.check_changed_request(env, Path(tmp))
                self.assertEqual(run.call_args.args[0][-2:], ["--", build.REQUEST_PATH])
            for code in (0, 128):
                with patch.object(build.subprocess, "run", return_value=Mock(returncode=code)):
                    with self.assertRaises(ValueError):
                        build.check_changed_request(env, Path(tmp))
            event.write_text(json.dumps({"before": "d" * 40, "after": "e" * 40}))
            with self.assertRaises(ValueError):
                build.check_changed_request(env, Path(tmp))


if __name__ == "__main__":
    unittest.main()
