"""Reject incomplete or mixed Android release bundles before upload/publication."""
import argparse
import hashlib
import json
import io
from pathlib import Path
import sys
import zipfile


DOWNLOADS = ('PGS.apk', 'PGS-Root.apk', 'PGS-Root-module.zip')
LEGACY_DOWNLOADS = ('PGRazor.apk', 'PGRazor-Root.apk', 'PGRazor-Root-module.zip')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify(folder, tag, *, legacy_names=False):
    folder = Path(folder)
    downloads = LEGACY_DOWNLOADS if legacy_names else DOWNLOADS
    other_names = DOWNLOADS if legacy_names else LEGACY_DOWNLOADS
    if any((folder / name).exists() for name in other_names):
        raise ValueError('Mixed or unexpected release artifact names')
    for name in (*downloads, 'build-info.json', 'root-build-info.json', 'SHA256SUMS.txt'):
        if not (folder / name).is_file() or not (folder / name).stat().st_size:
            raise ValueError('Missing or empty release file: ' + name)
    checksums = {}
    for line in (folder / 'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        checksum, name = line.split('  ', 1)
        if name in checksums:
            raise ValueError('Duplicate checksum: ' + name)
        checksums[name] = checksum
    actual = {name: digest(folder / name) for name in downloads}
    if checksums != actual:
        raise ValueError('Release checksums do not match the three downloads')
    normal = json.loads((folder / 'build-info.json').read_text(encoding='utf-8'))
    root = json.loads((folder / 'root-build-info.json').read_text(encoding='utf-8'))
    if (normal['apk_sha256'] != actual[downloads[0]] or
            root['installer_sha256'] != actual[downloads[1]] or
            root['module_sha256'] != actual[downloads[2]]):
        raise ValueError('Build receipts do not match the downloads')
    if (normal['game_version'] != root['target']['versionName'] or
            normal['game_version_code'] != root['target']['versionCode']):
        raise ValueError('Rooted and non-rooted game targets differ')
    if root['version'] != tag:
        raise ValueError('Rooted build version differs from release tag')
    with zipfile.ZipFile(folder / downloads[0]) as apk:
        mode_paths = [n for n in ('assets/pgs/mode.json', 'assets/pgrazor/mode.json') if n in apk.namelist()]
        if len(mode_paths) != 1: raise ValueError('Expected exactly one PGS mode asset')
        mode = json.loads(apk.read(mode_paths[0]))
        if not legacy_names and (mode_paths != ['assets/pgs/mode.json'] or mode.get('pgsVersion') != tag):
            raise ValueError('Non-rooted PGS build version or canonical mode asset differs from release tag')
        if mode.get('pgsVersion', mode.get('pgrazorVersion')) != tag or ('pgrazorVersion' in mode and mode['pgrazorVersion'] != tag):
            raise ValueError('Non-rooted build version differs from release tag')
    with zipfile.ZipFile(folder / downloads[2]) as module:
        props = dict(line.split('=', 1) for line in module.read('module.prop').decode().splitlines()
                     if '=' in line)
        if props.get('id') != 'pgrazor' or props.get('version') != tag:
            raise ValueError('Module identity/version differs from release tag')
    with zipfile.ZipFile(folder / downloads[1]) as installer:
        embedded = [name for name in installer.namelist() if name.startswith('assets/') and name.endswith('.zip')]
        if len(embedded) != 1:
            raise ValueError('Installer must contain exactly one module ZIP')
        with installer.open(embedded[0]) as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != actual[downloads[2]]:
                raise ValueError('Installer embeds a different module from the published ZIP')
    return actual


def verified_zip(archive):
    names = archive.namelist()
    if len(names) != len(set(names)) or archive.testzip() is not None:
        raise ValueError('Corrupt ZIP or duplicate members in candidate')


def stream_digest(archive, name):
    with archive.open(name) as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify_candidate_metadata(folder, tag, source_commit):
    """Cross-check the three variants, original input, source and shared controls DEX."""
    folder = Path(folder)
    actual = verify(folder, tag)
    normal = json.loads((folder / 'build-info.json').read_text(encoding='utf-8'))
    root = json.loads((folder / 'root-build-info.json').read_text(encoding='utf-8'))
    receipt = json.loads((folder / 'PGS.json').read_text(encoding='utf-8'))
    if (not source_commit or normal.get('source_commit') != source_commit
            or root.get('source_commit') != source_commit
            or not normal.get('input_sha256') or root.get('input_sha256') != normal['input_sha256']
            or normal.get('device_tested') is not False
            or root.get('installed') is not False or root.get('device_tested') is not False
            or any(receipt.get(key) is not False for key in
                   ('device_tested', 'in_place_update_tested', 'publish_ready'))
            or receipt.get('pgs_version') != tag or receipt.get('sha256') != actual[DOWNLOADS[0]]
            or receipt.get('version_code') != normal.get('apk_version_code')):
        raise ValueError('Candidate provenance, version or device-test state mismatch')
    with zipfile.ZipFile(folder / DOWNLOADS[0]) as apk:
        controls_digest = stream_digest(apk, receipt['controls_dex'])
    with zipfile.ZipFile(folder / DOWNLOADS[2]) as module:
        verified_zip(module)
        if (stream_digest(module, 'pgs/classes.dex') != controls_digest
                or root.get('dex_sha256') != controls_digest
                or stream_digest(module, 'pgs/payload.zip') != root.get('payload_sha256')):
            raise ValueError('Root module does not contain the verified shared DEX/payload')
        with zipfile.ZipFile(io.BytesIO(module.read('pgs/payload.zip'))) as payload:
            verified_zip(payload)
            target = json.loads(payload.read('pgs/rooted/target.json'))
            mode = json.loads(payload.read('pgs/mode.json'))
            if (target != root['target'] or mode.get('pgsVersion') != tag
                    or mode.get('compiledGameplay') is not True or mode.get('gadget') is not False
                    or root.get('abis') != ['arm64-v8a', 'x86_64']
                    or mode.get('runtimeAbis') != root['abis']):
                raise ValueError('Root payload target, version or ABI mismatch')
            for abi in root['abis']:
                for name in ('libpgs-core.so', 'libpgs-art.so'):
                    if payload.getinfo('pgs/' + abi + '/' + name).file_size <= 0:
                        raise ValueError('Missing Root runtime library')
                if module.getinfo('zygisk/' + abi + '.so').file_size <= 0:
                    raise ValueError('Missing Root loader')
    return actual


def verify_signed_candidate(folder, tag, source_commit):
    """Additional Android signature and installer manifest checks for signed candidates."""
    actual = verify_candidate_metadata(folder, tag, source_commit)
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'pgs'))
    import axml
    import nonroot
    import pgs_update
    import rooted_installer
    folder = Path(folder)
    root = json.loads((folder / 'root-build-info.json').read_text(encoding='utf-8'))
    if (root['target'].get('package') != pgs_update.GAME_PACKAGE
            or root['target'].get('certificateSha256') != nonroot.NIANTIC_CERT_SHA256):
        raise ValueError('Unexpected original game package or signing certificate')
    for name in DOWNLOADS[:2]:
        if pgs_update.cert_digests(folder / name) != [pgs_update.PGS_SIGNER]:
            raise ValueError('Candidate APK signing certificate mismatch: ' + name)
    with zipfile.ZipFile(folder / DOWNLOADS[1]) as installer:
        verified_zip(installer)
        manifest = axml.inspect_manifest(installer.read('AndroidManifest.xml'))
        if (manifest['package'] != rooted_installer.PACKAGE
                or manifest['versionName'] != tag.removeprefix('v')
                or manifest['versionCode'] != rooted_installer.installer_version_code(tag)
                or manifest['split'] is not None):
            raise ValueError('Root installer manifest identity mismatch')
    return actual


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=Path)
    parser.add_argument('--tag', required=True)
    parser.add_argument('--legacy-names', action='store_true', help='Verify archived upstream-named bundles only')
    parser.add_argument('--signed-candidate', action='store_true')
    parser.add_argument('--source-commit')
    args = parser.parse_args()
    if args.signed_candidate:
        if args.legacy_names or not args.source_commit:
            parser.error('--signed-candidate requires --source-commit and canonical PGS names')
        result = verify_signed_candidate(args.folder, args.tag, args.source_commit)
    else:
        result = verify(args.folder, args.tag, legacy_names=args.legacy_names)
    for name, checksum in result.items():
        print(checksum + '  ' + name)
