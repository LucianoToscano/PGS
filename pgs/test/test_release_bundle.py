"""Exercise release rejection with real ZIPs and mismatched publication artifacts."""
import json
import io
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import verify_release


class ReleaseBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.tag = 'v0.2.6'
        with zipfile.ZipFile(self.folder / 'PGS.apk', 'w') as apk:
            apk.writestr('assets/pgs/mode.json', json.dumps({'version': '17.24.2', 'pgsVersion': self.tag}))
        with zipfile.ZipFile(self.folder / 'PGS-Root-module.zip', 'w') as module:
            module.writestr('module.prop', 'id=pgrazor\nversion=' + self.tag + '\n')
        self.installer(self.folder / 'PGS-Root-module.zip')
        self.receipts()

    def installer(self, module):
        with zipfile.ZipFile(self.folder / 'PGS-Root.apk', 'w') as apk:
            apk.write(module, 'assets/module.zip')

    def receipts(self, names=verify_release.DOWNLOADS):
        hashes = {name: verify_release.digest(self.folder / name) for name in names}
        (self.folder / 'SHA256SUMS.txt').write_text(''.join(h + '  ' + n + '\n' for n, h in hashes.items()))
        (self.folder / 'build-info.json').write_text(json.dumps({
            'game_version': '0.435.2', 'game_version_code': 2026110702, 'apk_sha256': hashes[names[0]]}))
        (self.folder / 'root-build-info.json').write_text(json.dumps({
            'version': self.tag, 'target': {'versionName': '0.435.2', 'versionCode': 2026110702},
            'installer_sha256': hashes[names[1]], 'module_sha256': hashes[names[2]]}))

    def test_signed_candidate_metadata_and_cross_variant_dex(self):
        controls = b"shared controls fixture"
        payload = io.BytesIO()
        abis = ['arm64-v8a', 'x86_64']
        target = {'versionName': '0.435.2', 'versionCode': 2026110702}
        with zipfile.ZipFile(payload, 'w') as data:
            data.writestr('pgs/rooted/target.json', json.dumps(target))
            data.writestr('pgs/mode.json', json.dumps({'pgsVersion': self.tag,
                'compiledGameplay': True, 'gadget': False, 'runtimeAbis': abis}))
            for abi in abis:
                for library in ('libpgs-core.so', 'libpgs-art.so'):
                    data.writestr('pgs/' + abi + '/' + library, b'fixture')
        def make_bundle(root_controls):
            with zipfile.ZipFile(self.folder / 'PGS.apk', 'w') as apk:
                apk.writestr('assets/pgs/mode.json', json.dumps({'pgsVersion': self.tag}))
                apk.writestr('classes2.dex', controls)
            with zipfile.ZipFile(self.folder / 'PGS-Root-module.zip', 'w') as module:
                module.writestr('module.prop', 'id=pgrazor\nversion=' + self.tag + '\n')
                module.writestr('pgs/classes.dex', root_controls)
                module.writestr('pgs/payload.zip', payload.getvalue())
                for abi in abis:
                    module.writestr('zygisk/' + abi + '.so', b'fixture')
            self.installer(self.folder / 'PGS-Root-module.zip')
            self.receipts()
            commit = 'a' * 40
            for filename, additions in (
                ('build-info.json', {'source_commit': commit, 'input_sha256': 'b' * 64,
                                     'device_tested': False, 'apk_version_code': 2026110703}),
                ('root-build-info.json', {'source_commit': commit, 'input_sha256': 'b' * 64,
                    'device_tested': False, 'installed': False, 'abis': abis,
                    'dex_sha256': hashlib.sha256(root_controls).hexdigest(),
                    'payload_sha256': hashlib.sha256(payload.getvalue()).hexdigest()})):
                path = self.folder / filename
                path.write_text(json.dumps(dict(json.loads(path.read_text()), **additions)))
            (self.folder / 'PGS.json').write_text(json.dumps({'pgs_version': self.tag,
                'sha256': verify_release.digest(self.folder / 'PGS.apk'), 'version_code': 2026110703,
                'controls_dex': 'classes2.dex', 'device_tested': False,
                'in_place_update_tested': False, 'publish_ready': False}))
            return commit
        commit = make_bundle(controls)
        self.assertEqual(set(verify_release.verify_candidate_metadata(self.folder, self.tag, commit)),
                         set(verify_release.DOWNLOADS))
        with self.assertRaisesRegex(ValueError, 'provenance'):
            verify_release.verify_candidate_metadata(self.folder, self.tag, 'c' * 40)
        make_bundle(b'different controls')
        with self.assertRaisesRegex(ValueError, 'shared DEX'):
            verify_release.verify_candidate_metadata(self.folder, self.tag, commit)

    def test_complete_bundle(self):
        self.assertEqual(set(verify_release.verify(self.folder, self.tag)), set(verify_release.DOWNLOADS))

    def test_canonical_version_metadata(self):
        with zipfile.ZipFile(self.folder / verify_release.DOWNLOADS[0], 'w') as apk:
            apk.writestr('assets/pgs/mode.json', json.dumps({'version': '17.24.2', 'pgsVersion': self.tag, 'pgrazorVersion': self.tag}))
        self.receipts()
        self.assertEqual(set(verify_release.verify(self.folder, self.tag)), set(verify_release.DOWNLOADS))
        with zipfile.ZipFile(self.folder / verify_release.DOWNLOADS[0], 'w') as apk:
            apk.writestr('assets/pgs/mode.json', json.dumps({'pgsVersion': self.tag, 'pgrazorVersion': 'v0.2.5'}))
        self.receipts()
        with self.assertRaisesRegex(ValueError, 'Non-rooted build version'):
            verify_release.verify(self.folder, self.tag)

    def test_archived_bundle_requires_explicit_legacy_selection(self):
        for current, legacy in zip(verify_release.DOWNLOADS, verify_release.LEGACY_DOWNLOADS):
            (self.folder / current).rename(self.folder / legacy)
        with zipfile.ZipFile(self.folder / verify_release.LEGACY_DOWNLOADS[0], 'w') as apk:
            apk.writestr('assets/pgrazor/mode.json', json.dumps({'pgrazorVersion': self.tag}))
        self.receipts(verify_release.LEGACY_DOWNLOADS)
        with self.assertRaisesRegex(ValueError, 'unexpected release artifact names'):
            verify_release.verify(self.folder, self.tag)
        self.assertEqual(set(verify_release.verify(self.folder, self.tag, legacy_names=True)), set(verify_release.LEGACY_DOWNLOADS))

    def test_mixed_artifact_names_rejected(self):
        (self.folder / verify_release.LEGACY_DOWNLOADS[0]).write_bytes(b'old')
        with self.assertRaisesRegex(ValueError, 'Mixed'):
            verify_release.verify(self.folder, self.tag)

    def test_current_bundle_rejects_old_mode_path(self):
        with zipfile.ZipFile(self.folder / verify_release.DOWNLOADS[0], 'w') as apk:
            apk.writestr('assets/pgrazor/mode.json', json.dumps({'pgrazorVersion': self.tag}))
        self.receipts()
        with self.assertRaisesRegex(ValueError, 'canonical mode asset'):
            verify_release.verify(self.folder, self.tag)

    def test_missing_download_blocks_publication(self):
        (self.folder / 'PGS-Root-module.zip').unlink()
        with self.assertRaisesRegex(ValueError, 'Missing'):
            verify_release.verify(self.folder, self.tag)

    def test_corrupted_download_blocks_publication(self):
        with (self.folder / 'PGS.apk').open('ab') as stream:
            stream.write(b'changed')
        with self.assertRaisesRegex(ValueError, 'checksums'):
            verify_release.verify(self.folder, self.tag)

    def test_installer_with_different_module_even_when_receipts_match(self):
        other = self.folder / 'old.zip'
        other.write_bytes(b'old module')
        self.installer(other)
        self.receipts()
        with self.assertRaisesRegex(ValueError, 'different module'):
            verify_release.verify(self.folder, self.tag)

    def test_wrong_game_target(self):
        path = self.folder / 'root-build-info.json'
        value = json.loads(path.read_text())
        value['target']['versionCode'] += 1
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, 'game targets'):
            verify_release.verify(self.folder, self.tag)

    def test_stale_nonroot_apk_even_when_receipts_match(self):
        with zipfile.ZipFile(self.folder / 'PGS.apk', 'w') as apk:
            apk.writestr('assets/pgs/mode.json', json.dumps({'version': '17.24.2', 'pgsVersion': 'v0.2.5'}))
        self.receipts()
        with self.assertRaisesRegex(ValueError, 'Non-rooted PGS build version'):
            verify_release.verify(self.folder, self.tag)

    def test_wrong_release_tag(self):
        with self.assertRaisesRegex(ValueError, 'Rooted build version'):
            verify_release.verify(self.folder, 'v0.2.7')


if __name__ == '__main__':
    unittest.main()
