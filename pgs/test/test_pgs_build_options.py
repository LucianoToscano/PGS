"""Regression tests for PGS-first build settings without SDK or signing keys."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build
from upstream_identity import upstream_name


class PgsBuildOptionTests(unittest.TestCase):
    def test_build_version_preserves_pgs_priority(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "VERSION").write_text("v0.0.2", encoding="utf-8")
            with patch.dict(build.os.environ, {}, clear=True):
                self.assertEqual(build.release_version(root), "v0.0.2")
            with patch.dict(build.os.environ, {"PGS_VERSION": "v0.1.2"}, clear=True):
                self.assertEqual(build.release_version(root), "v0.1.2")
            with patch.dict(build.os.environ,
                            {"PGS_VERSION": "v0.0.4"}, clear=True):
                self.assertEqual(build.release_version(root), "v0.0.4")
            with patch.dict(build.os.environ, {"PGS_VERSION": "bad version"}, clear=True):
                with self.assertRaisesRegex(ValueError, "Invalid PGS version"):
                    build.release_version(root)

    def test_workflows_use_pgs_nonsecret_build_options(self):
        workflows = Path(__file__).resolve().parents[2] / '.github' / 'workflows'
        for name in ('ci.yml', 'pgs-v0.0.4-candidate.yml'):
            with self.subTest(workflow=name):
                source = (workflows / name).read_text(encoding='utf-8')
                self.assertIn('PGS_BUILD_TOOLS:', source)
                self.assertIn('PGS_ANDROID_PLATFORM:', source)
                if name == 'pgs-v0.0.4-candidate.yml':
                    self.assertIn('PGS_VERSION:', source)

    def test_historical_publication_workflows_use_pgs_identity(self):
        workflows = Path(__file__).resolve().parents[2] / '.github' / 'workflows'
        for name in ('release.yml', 'pgs-v0.0.4-release.yml'):
            with self.subTest(workflow=name):
                flow = (workflows / name).read_text(encoding='utf-8')
                # Reject every case variant of the old brand in release workflows.
                self.assertNotIn(upstream_name().lower(), flow.lower())
                # Every release workflow references the PGS identity.
                self.assertIn('PGS', flow)
        # The manual historical release is dispatch-driven (no unattended push release).
        flow = (workflows / 'release.yml').read_text(encoding='utf-8')
        self.assertIn('  workflow_dispatch:', flow)
        self.assertNotIn('\n  push:', flow)
        self.assertNotIn('\n  pull_request:', flow)
        # The v0.0.4 release workflow is trigger-driven on the reference branch (push) and also
        # admits manual dispatch; both are legitimate in the reference.
        flow = (workflows / 'pgs-v0.0.4-release.yml').read_text(encoding='utf-8')
        self.assertIn('on:', flow)
        self.assertIn('  workflow_dispatch:', flow)


if __name__ == "__main__":
    unittest.main()
