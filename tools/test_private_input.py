"""Offline tests for private input retrieval headers; no real credentials or network."""
import os
import unittest
from unittest.mock import patch
from urllib.request import Request

from private_input import HttpsRedirect, input_headers


class PrivateInputHeaderTests(unittest.TestCase):
    asset = "https://api.github.com/repos/example/private-inputs/releases/assets/123"

    def test_scoped_token_preferred_over_job_token(self):
        with patch.dict(os.environ, {"PGS_INPUT_TOKEN": "synthetic-scoped", "GITHUB_TOKEN": "synthetic-job"}, clear=True):
            self.assertEqual(input_headers(self.asset), {
                "Accept": "application/octet-stream", "Authorization": "Bearer synthetic-scoped"})

    def test_job_token_fallback(self):
        with patch.dict(os.environ, {"GITHUB_TOKEN": "synthetic-job"}, clear=True):
            self.assertEqual(input_headers(self.asset)["Authorization"], "Bearer synthetic-job")

    def test_missing_token_fails(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(SystemExit, "requires an authorized repository token"):
                input_headers(self.asset)

    def test_scoped_token_restricted_to_asset_api(self):
        with patch.dict(os.environ, {"PGS_INPUT_TOKEN": "synthetic-scoped"}, clear=True):
            for url in ("https://example.com/input.apkm",
                        "https://api.github.com.evil.example/repos/a/b/releases/assets/1",
                        "https://api.github.com/user",
                        "https://api.github.com:443/repos/a/b/releases/assets/1",
                        self.asset + "?token=example",
                        "https://example@api.github.com/repos/a/b/releases/assets/1",
                        "http://api.github.com/repos/a/b/releases/assets/1"):
                with self.subTest(url=url), self.assertRaises(SystemExit):
                    input_headers(url)

    def test_direct_https_without_github_specific_token(self):
        with patch.dict(os.environ, {"GITHUB_TOKEN": "synthetic-job"}, clear=True):
            self.assertEqual(input_headers("https://example.com/private/input.apkm"), {})
            with self.assertRaisesRegex(SystemExit, "HTTPS"):
                input_headers("http://example.com/input.apkm")

    def test_cross_host_redirect_strips_authorization(self):
        request = Request(self.asset, headers={"Authorization": "Bearer synthetic-scoped"})
        redirect = HttpsRedirect().redirect_request(request, None, 302, "Found", {},
                                                    "https://objects.example.com/signed-object")
        self.assertIsNone(redirect.get_header("Authorization"))
        with self.assertRaisesRegex(ValueError, "Insecure redirect"):
            HttpsRedirect().redirect_request(request, None, 302, "Found", {},
                                             "http://objects.example.com/object")


if __name__ == "__main__":
    unittest.main()
