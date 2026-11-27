"""Offline regression tests for bounded, hash-pinned build dependency downloads."""
from email.message import Message
from pathlib import Path
import hashlib
import io
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import dex_bridges


class DexDependencyRetryTests(unittest.TestCase):
    data = b"synthetic pinned jar"
    item = {"url": "https://example.invalid/fixture.jar",
            "sha256": hashlib.sha256(data).hexdigest()}

    def http_error(self, code, delay=None):
        headers = Message()
        if delay is not None:
            headers["Retry-After"] = str(delay)
        return HTTPError(self.item["url"], code, "synthetic failure", headers, io.BytesIO())

    def test_rate_limit_respects_retry_after_and_verifies_hash(self):
        with patch.object(dex_bridges.urllib.request, "urlopen",
                          side_effect=[self.http_error(429, 17), io.BytesIO(self.data)]) as fetch, patch.object(
                              dex_bridges.time, "sleep") as sleep:
            self.assertEqual(dex_bridges.download_dependency(self.item), self.data)
        self.assertEqual(fetch.call_count, 2)
        sleep.assert_called_once_with(17)

    def test_retry_budget_is_bounded(self):
        errors = [self.http_error(503) for _ in range(dex_bridges.MAX_ATTEMPTS)]
        with patch.object(dex_bridges.urllib.request, "urlopen", side_effect=errors) as fetch, patch.object(
                dex_bridges.time, "sleep") as sleep:
            with self.assertRaisesRegex(RuntimeError, "HTTP 503"):
                dex_bridges.download_dependency(self.item)
        self.assertEqual(fetch.call_count, 4)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [5, 10, 20])

    def test_long_server_delay_does_not_trigger_early_retry(self):
        with patch.object(dex_bridges.urllib.request, "urlopen", side_effect=self.http_error(429, 120)) as fetch, patch.object(
                dex_bridges.time, "sleep") as sleep:
            with self.assertRaisesRegex(RuntimeError, "longer wait"):
                dex_bridges.download_dependency(self.item)
        self.assertEqual(fetch.call_count, 1)
        sleep.assert_not_called()

    def test_permanent_http_and_tls_errors_are_not_retried(self):
        for error in (self.http_error(404), URLError("certificate verification failed")):
            with self.subTest(error=type(error).__name__), patch.object(
                    dex_bridges.urllib.request, "urlopen", side_effect=error) as fetch, patch.object(
                        dex_bridges.time, "sleep") as sleep:
                with self.assertRaises(RuntimeError):
                    dex_bridges.download_dependency(self.item)
            self.assertEqual(fetch.call_count, 1)
            sleep.assert_not_called()

    def test_transient_timeout_recovers(self):
        with patch.object(dex_bridges.urllib.request, "urlopen",
                          side_effect=[URLError(TimeoutError()), io.BytesIO(self.data)]), patch.object(
                              dex_bridges.time, "sleep") as sleep:
            self.assertEqual(dex_bridges.download_dependency(self.item), self.data)
        sleep.assert_called_once_with(5)

    def test_wrong_hash_and_oversize_never_retry(self):
        for limit, data in ((1024, b"tampered"), (2, self.data)):
            with self.subTest(limit=limit), patch.object(dex_bridges, "MAX_DOWNLOAD_BYTES", limit), patch.object(
                    dex_bridges.urllib.request, "urlopen", return_value=io.BytesIO(data)) as fetch, patch.object(
                        dex_bridges.time, "sleep") as sleep:
                with self.assertRaises(RuntimeError):
                    dex_bridges.download_dependency(self.item)
            self.assertEqual(fetch.call_count, 1)
            sleep.assert_not_called()

    def test_verified_cache_only_and_corruption_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, cache = root / "tools", root / "cache"
            manifest.mkdir()
            (manifest / "dependencies.json").write_text(json.dumps([self.item]), encoding="utf-8")
            with patch.object(dex_bridges, "TOOLS", manifest), patch.object(dex_bridges, "CACHE", cache), patch.object(
                    dex_bridges.urllib.request, "urlopen", return_value=io.BytesIO(self.data)) as fetch:
                with self.assertRaisesRegex(RuntimeError, "Missing pinned"):
                    dex_bridges.dependencies()
                fetch.assert_not_called()
                paths = dex_bridges.dependencies(download=True)
                self.assertEqual(paths, [cache / "fixture.jar"])
                self.assertEqual(paths[0].read_bytes(), self.data)
                self.assertEqual(list(cache.iterdir()), paths)
                self.assertEqual(dex_bridges.dependencies(), paths)
                self.assertEqual(fetch.call_count, 1)
                paths[0].write_bytes(b"tampered cache")
                with self.assertRaisesRegex(RuntimeError, "checksum mismatch"):
                    dex_bridges.dependencies(download=True)
                self.assertEqual(fetch.call_count, 1)


if __name__ == "__main__":
    unittest.main()
