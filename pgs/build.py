"""Offline build using the installed Android SDK and JDK; no Gradle download."""
from pathlib import Path
import argparse
import re
import os
import shutil
import subprocess
import zipfile
import uuid
import hashlib
import json

ROOT = Path(__file__).resolve().parent

def build_setting(primary, legacy, default=None, environ=None):
    """Prefer a PGS build setting while retaining the previous environment alias.

    Values are selected without modifying the process environment, so existing
    GitHub Actions secrets and SDK configurations are not rewritten. Empty
    values behave as unset. These are NON-SECRET build options only.
    """
    env = os.environ if environ is None else environ
    return env.get(primary) or env.get(legacy) or default


def source_fingerprints(root):
    paths = [*sorted((root/'src').rglob('*.java')), root/'VERSION', root/'AndroidManifest.xml']
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}

def release_version(root):
    version = build_setting('PGS_VERSION', 'PGRAZOR_VERSION', (root/'VERSION').read_text(encoding='utf-8').strip())
    if not re.fullmatch(r'v?[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.-]+)?', version):
        raise ValueError('Invalid PGS version')
    return 'v' + version.removeprefix('v')

def map_icon_assets():
    """Bundled POI marker PNGs plus the Pokemon name table for assets/pgs/map-icons.

    Only direct *.png children of assets/map-icons are taken (no recursion/traversal), and the
    archive name is always the bare file name so a crafted source path cannot escape the folder.
    pokemon-names.json (the raid-boss name lookup read by the Java map) is included under the same
    bare-name, no-symlink, stays-inside-the-folder checks. Both preview and nonroot packaging reuse
    this helper, so the name table reaches the APK at assets/pgs/map-icons/pokemon-names.json.
    """
    source = ROOT / 'assets/map-icons'
    icons = {}
    if source.is_dir():
        for path in sorted(source.glob('*.png')):
            if path.is_symlink() or not path.resolve().is_relative_to(source.resolve()):
                raise ValueError("Map icon escapes asset directory")
            if path.is_file():
                icons.setdefault(path.name, path)
        names = source / 'pokemon-names.json'
        if names.is_file() and not names.is_symlink() and names.resolve().is_relative_to(source.resolve()):
            icons.setdefault(names.name, names)
    return icons

def feed_icon_assets():
    """Only numeric base-species PNGs under the bundled feed sprite directory."""
    source = ROOT / 'assets/feed-icons/pokemon'
    icons = {}
    for path in sorted(source.glob('*.png')):
        if not path.stem.isascii() or not path.stem.isdecimal():
            continue
        if path.is_symlink() or not path.resolve().is_relative_to(source.resolve()):
            raise ValueError('Feed icon escapes asset directory')
        if path.is_file():
            icons[path.name] = path
    return icons

SDK = Path(os.environ.get('ANDROID_HOME', str(Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'Android/Sdk')))
TOOLS = SDK / 'build-tools' / build_setting('PGS_BUILD_TOOLS', 'PGRAZOR_BUILD_TOOLS', '36.1.0')
ANDROID = SDK / 'platforms' / build_setting('PGS_ANDROID_PLATFORM', 'PGRAZOR_ANDROID_PLATFORM', 'android-36.1') / 'android.jar'
BUILD = ROOT / 'build'

def android_tool(name):
    """Resolve an Android SDK build tool for the current host OS."""
    if os.name == 'nt':
        suffix = '.bat' if name in ('d8', 'apksigner') else '.exe'
    else:
        suffix = ''
    return TOOLS / (name + suffix)

def run(*args):
    subprocess.run([str(a) for a in args], cwd=ROOT, check=True)

def signing_setting(name, default=None, environ=None):
    """Use PGS signing variables first; retain the existing external alias."""
    env = os.environ if environ is None else environ
    return env.get('PGS_' + name) or env.get('PGRAZOR_' + name) or default


def signing_args():
    configured = any(name in os.environ for name in ('PGS_KEYSTORE', 'PGRAZOR_KEYSTORE'))
    selected = signing_setting('KEYSTORE')
    if configured:
        if not selected:
            raise RuntimeError('Configured signing key path is empty')
        key = Path(selected)
        alias = signing_setting('KEY_ALIAS')
        store = signing_setting('STORE_PASSWORD')
        password = signing_setting('KEY_PASSWORD')
        if not key.is_file() or not alias or not store or not password:
            raise RuntimeError('Configured signing key, alias or password environment variables are missing')
    else:
        # Reuse an existing local development key; never substitute a release key.
        legacy_key = BUILD / 'pgs-development.jks'
        key = legacy_key if legacy_key.exists() else BUILD / 'pgs-development.jks'
        alias = signing_setting('KEY_ALIAS', 'pgs' if legacy_key.exists() else 'pgs')
        store = signing_setting('STORE_PASSWORD', 'android')
        password = signing_setting('KEY_PASSWORD', 'android')
    os.environ['PGS_STORE_PASSWORD'] = store
    os.environ['PGS_KEY_PASSWORD'] = password
    if not configured and not key.exists():
        run('keytool','-genkeypair','-keystore',key,'-storepass:env','PGS_STORE_PASSWORD','-keypass:env','PGS_KEY_PASSWORD','-alias',alias,'-keyalg','RSA','-keysize','2048','-validity','3650','-dname','CN=PGS Local Development')
    return ['--ks',key,'--ks-pass','env:PGS_STORE_PASSWORD','--key-pass','env:PGS_KEY_PASSWORD','--ks-key-alias',alias]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--test-only', action='store_true', help='Test coordinates and native ABI validation without the Android SDK')
    args = parser.parse_args()
    for folder in ['classes','dex','tests','input']:
        (BUILD / folder).mkdir(parents=True,exist_ok=True)
    (ROOT / 'input').mkdir(exist_ok=True)
    run('javac','-encoding','UTF-8','-d',BUILD/'tests',ROOT/'src/dev/pgs/MotionEngine.java',ROOT/'test/MotionTest.java',ROOT/'src/dev/pgs/RuntimeAbi.java',ROOT/'test/RuntimeAbiTest.java',ROOT/'src/dev/pgs/MapProjection.java',ROOT/'test/MapProjectionTest.java')
    run('java','-cp',BUILD/'tests','MotionTest')
    run('javac','-encoding','UTF-8','-d',BUILD/'tests',ROOT/'src/dev/pgs/MotionEngine.java',ROOT/'test/IdleWalkTest.java')
    run('java','-cp',BUILD/'tests','IdleWalkTest')
    run('javac','-encoding','UTF-8','-d',BUILD/'tests',ROOT/'src/dev/pgs/MotionEngine.java',ROOT/'src/dev/pgs/AutoWalkPlanner.java',ROOT/'test/AutoWalkTest.java')
    run('java','-cp',BUILD/'tests','AutoWalkTest')
    run('java','-cp',BUILD/'tests','RuntimeAbiTest')
    run('java','-cp',BUILD/'tests','MapProjectionTest')
    run('javac','-encoding','UTF-8','-d',BUILD/'tests',ROOT/'src/dev/pgs/MotionEngine.java',ROOT/'src/dev/pgs/LocationState.java',ROOT/'test/LocationStateTest.java')
    run('java','-cp',BUILD/'tests','LocationStateTest')
    run('javac','-encoding','UTF-8','-d',BUILD/'tests',ROOT/'src/dev/pgs/CameraSteering.java',ROOT/'test/CameraSteeringTest.java')
    run('java','-cp',BUILD/'tests','CameraSteeringTest')
    run('javac','-encoding','UTF-8','-d',BUILD/'tests',ROOT/'src/dev/pgs/CameraSteering.java',ROOT/'src/dev/pgs/CameraHeadingState.java',ROOT/'test/CameraHeadingStateTest.java')
    run('java','-cp',BUILD/'tests','CameraHeadingStateTest')
    run('javac','-encoding','UTF-8','-d',BUILD/'tests',ROOT/'src/dev/pgs/ShundoPacing.java',ROOT/'test/ShundoPacingTest.java')
    run('java','-cp',BUILD/'tests','dev.pgs.ShundoPacingTest')
    run('javac','-encoding','UTF-8','-d',BUILD/'tests',ROOT/'src/dev/pgs/FeedSpots.java',ROOT/'test/FeedSpotsTest.java')
    run('java','-cp',BUILD/'tests','dev.pgs.FeedSpotsTest')
    run('javac','-encoding','UTF-8','-d',BUILD/'tests',ROOT/'src/dev/pgs/UpdateRules.java',ROOT/'test/UpdateRulesTest.java')
    run('java','-cp',BUILD/'tests','dev.pgs.UpdateRulesTest')
    if args.test_only: return
    version = release_version(ROOT)
    # Fresh outputs prevent a failed compiler from silently reusing old classes.
    classes=BUILD/('compile-'+uuid.uuid4().hex[:12]); classes.mkdir()
    version_source = classes/'BuildVersion.java'
    version_source.write_text('package dev.pgs; final class BuildVersion { static final String NAME = "' + version + '"; }\n', encoding='utf-8')
    run('javac','-encoding','UTF-8','-source','8','-target','8','-classpath',ANDROID,'-d',classes,version_source,*sorted((ROOT/'src').rglob('*.java')))
    for name in ['PreviewActivity','BootstrapProvider','LogActivity','LogExport','Control','Pad','MotionEngine','RuntimeAbi','MapProjection','WorldMapDialog','SavedPlaces','LocationState','CameraSteering','CameraHeadingState']:
        if not (classes/f'dev/pgs/{name}.class').is_file():
            raise RuntimeError(f'Android compilation produced no {name} class. Check SDK access and javac output above.')
    run('javac','-encoding','UTF-8','-classpath',str(ANDROID)+os.pathsep+str(classes),'-d',BUILD/'tests',ROOT/'src/dev/pgs/SavedPlaces.java',ROOT/'test/SavedPlacesValidationTest.java')
    run('java','-cp',BUILD/'tests','SavedPlacesValidationTest')
    jar = BUILD/'controls.jar'
    with zipfile.ZipFile(jar,'w',zipfile.ZIP_DEFLATED) as out:
        for path in classes.rglob('*.class'): out.write(path,path.relative_to(classes).as_posix())
    run(android_tool('d8'),'--min-api','28','--lib',ANDROID,'--output',BUILD/'dex',jar)
    unsigned=BUILD/'preview-unsigned.apk'
    run(android_tool('aapt'),'package','-f','-M',ROOT/'AndroidManifest.xml','-I',ANDROID,'-F',unsigned)
    with zipfile.ZipFile(unsigned,'a',zipfile.ZIP_DEFLATED) as out:
        out.write(BUILD/'dex/classes.dex','classes.dex')
        for name,path in map_icon_assets().items(): out.write(path,'assets/pgs/map-icons/'+name)
        for name,path in feed_icon_assets().items(): out.write(path,'assets/pgs/feed-icons/pokemon/'+name)
    run(android_tool('zipalign'),'-f','4',unsigned,BUILD/'preview-aligned.apk')
    apk=BUILD/'pgs-preview.apk'
    run(android_tool('apksigner'),'sign',*signing_args(),'--out',apk,BUILD/'preview-aligned.apk')
    run(android_tool('apksigner'),'verify',apk)
    shutil.copyfile(BUILD/'dex/classes.dex',BUILD/'pgs.dex')
    fingerprints=source_fingerprints(ROOT)
    (BUILD/'build-state.json').write_text(json.dumps({'version':version,'sources':fingerprints,'dex_sha256':hashlib.sha256((BUILD/'pgs.dex').read_bytes()).hexdigest()},indent=2),encoding='utf-8')
    print('Built:',apk)

if __name__=='__main__': main()
