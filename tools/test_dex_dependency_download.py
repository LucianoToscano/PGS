"""Offline regression tests for Maven rate-limit recovery and strict artifact pins."""
import hashlib
from io import BytesIO
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pgs"))
import dex_bridges as dex


class DependencyDownloadTests(unittest.TestCase):
    content = b"pinned jar fixture"
    item = {"url": dex.CENTRAL + "example/tool/1/tool-1.jar",
            "sha256": hashlib.sha256(content).hexdigest()}

    def http_error(self, code, headers=None):
        return urllib.error.HTTPError(self.item["url"], code, "test", headers or {}, None)

    def test_rate_limit_waits_then_uses_verified_mirror(self):
        with patch.object(dex.urllib.request, "urlopen",
                          side_effect=[self.http_error(429, {"Retry-After": "12"}), BytesIO(self.content)]) as get, \
                patch.object(dex.time, "sleep") as sleep:
            self.assertEqual(dex.download_pinned(self.item), self.content)
        sleep.assert_called_once_with(12)
        self.assertEqual(get.call_args_list[1].args[0].full_url,
                         dex.CENTRAL_MIRROR + "example/tool/1/tool-1.jar")

    def test_long_retry_after_is_not_bypassed(self):
        with patch.object(dex.urllib.request, "urlopen", side_effect=self.http_error(
                429, {"Retry-After": "3600"})) as get, patch.object(dex.time, "sleep") as sleep:
            with self.assertRaisesRegex(RuntimeError, "retry delay"):
                dex.download_pinned(self.item)
        get.assert_called_once()
        sleep.assert_not_called()

    def test_checksum_mismatch_is_not_retried(self):
        with patch.object(dex.urllib.request, "urlopen", return_value=BytesIO(b"corrupted")) as get:
            with self.assertRaisesRegex(RuntimeError, "checksum mismatch"):
                dex.download_pinned(self.item)
        get.assert_called_once()

    def test_permanent_http_failure_is_not_retried(self):
        with patch.object(dex.urllib.request, "urlopen", side_effect=self.http_error(404)) as get:
            with self.assertRaisesRegex(RuntimeError, "404"):
                dex.download_pinned(self.item)
        get.assert_called_once()

    def test_network_retries_are_bounded(self):
        with patch.object(dex.urllib.request, "urlopen", side_effect=urllib.error.URLError("offline")) as get, \
                patch.object(dex.time, "sleep") as sleep:
            with self.assertRaisesRegex(RuntimeError, "retry limit"):
                dex.download_pinned(self.item)
        self.assertEqual(get.call_count, 4)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [5, 10, 20])

    def test_atomic_cache_write(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(dex, "CACHE", Path(tmp)):
            jar = Path(tmp) / "tool.jar"
            dex.store_verified(jar, self.content)
            self.assertEqual(jar.read_bytes(), self.content)
            self.assertEqual(list(Path(tmp).iterdir()), [jar])


if __name__ == "__main__":
    unittest.main()
