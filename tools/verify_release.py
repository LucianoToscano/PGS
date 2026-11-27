"""Reject incomplete or mixed Android release bundles before upload/publication."""
import argparse
import hashlib
import json
from pathlib import Path
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
        candidates = ('assets/pgrazor/mode.json', 'assets/pgs/mode.json') if legacy_names else ('assets/pgs/mode.json',)
        mode_paths = [n for n in candidates if n in apk.namelist()]
        if not legacy_names and 'assets/pgrazor/mode.json' in apk.namelist() and 'assets/pgs/mode.json' not in apk.namelist():
            raise ValueError('Legacy pgrazor mode asset present; canonical mode asset assets/pgs/mode.json required')
        if len(mode_paths) != 1: raise ValueError('Expected exactly one PGS mode asset')
        mode = json.loads(apk.read(mode_paths[0]))
        if not legacy_names and (mode_paths != ['assets/pgs/mode.json'] or mode.get('pgsVersion') != tag):
            raise ValueError('Non-rooted PGS build version or canonical mode asset differs from release tag')
        if not legacy_names and mode.get('pgrazorVersion') not in (None, tag):
            raise ValueError('Non-rooted build version differs from release tag')
        if mode.get('pgsVersion', mode.get('pgsVersion')) != tag or ('pgsVersion' in mode and mode['pgsVersion'] != tag):
            raise ValueError('Non-rooted build version differs from release tag')
    with zipfile.ZipFile(folder / downloads[2]) as module:
        props = dict(line.split('=', 1) for line in module.read('module.prop').decode().splitlines()
                     if '=' in line)
        if props.get('id') != 'pgs' or props.get('version') != tag:
            raise ValueError('Module identity/version differs from release tag')
    with zipfile.ZipFile(folder / downloads[1]) as installer:
        embedded = [name for name in installer.namelist() if name.startswith('assets/') and name.endswith('.zip')]
        if len(embedded) != 1:
            raise ValueError('Installer must contain exactly one module ZIP')
        with installer.open(embedded[0]) as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != actual[downloads[2]]:
                raise ValueError('Installer embeds a different module from the published ZIP')
    return actual


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=Path)
    parser.add_argument('--tag', required=True)
    parser.add_argument('--legacy-names', action='store_true', help='Verify archived upstream-named bundles only')
    args = parser.parse_args()
    for name, checksum in verify(args.folder, args.tag, legacy_names=args.legacy_names).items():
        print(checksum + '  ' + name)
