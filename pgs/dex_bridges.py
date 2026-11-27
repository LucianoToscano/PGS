"""Build-time Java bridge migration using pinned dexlib2 (never shipped in the APK)."""
from pathlib import Path
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
import json
import os
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / 'tools/dex_bridge'
CACHE = ROOT / '.artifacts/native-migration/dex-tools'


def sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


MAX_DOWNLOAD_BYTES = 32 * 1024 * 1024
MAX_ATTEMPTS = 4
MAX_RETRY_AFTER = 60
TRANSIENT_HTTP = {408, 429, 500, 502, 503, 504}


def retry_delay(header, attempt):
    """Respect a server's requested delay within a bounded CI retry budget."""
    fallback = 5 * (2 ** attempt)
    if header:
        try:
            seconds = int(header)
        except ValueError:
            try:
                date = parsedate_to_datetime(header)
                if date.tzinfo is None:
                    date = date.replace(tzinfo=timezone.utc)
                seconds = (date - datetime.now(timezone.utc)).total_seconds()
            except (ValueError, TypeError, OverflowError):
                seconds = 0
        fallback = max(fallback, seconds)
    if fallback > MAX_RETRY_AFTER:
        raise RuntimeError("DEX dependency server requested a longer wait; retry the workflow later")
    return fallback


def download_dependency(item):
    """Retry transient availability failures only; never accept unpinned bytes."""
    for attempt in range(MAX_ATTEMPTS):
        try:
            with urllib.request.urlopen(item["url"], timeout=60) as response:
                data = response.read(MAX_DOWNLOAD_BYTES + 1)
        except urllib.error.HTTPError as error:
            code = error.code
            header = error.headers.get("Retry-After") if error.headers else None
            error.close()
            if code not in TRANSIENT_HTTP or attempt == MAX_ATTEMPTS - 1:
                raise RuntimeError(f"DEX dependency download failed (HTTP {code})") from None
            delay = retry_delay(header, attempt)
        except (TimeoutError, urllib.error.URLError) as error:
            if (isinstance(error, urllib.error.URLError)
                    and not isinstance(error.reason, TimeoutError)):
                raise RuntimeError("DEX dependency network or TLS failure") from None
            if attempt == MAX_ATTEMPTS - 1:
                raise RuntimeError("DEX dependency download timed out") from None
            delay = retry_delay(None, attempt)
        else:
            if len(data) > MAX_DOWNLOAD_BYTES:
                raise RuntimeError("DEX dependency exceeds the download size limit")
            if hashlib.sha256(data).hexdigest() != item["sha256"]:
                raise RuntimeError("Downloaded DEX dependency checksum mismatch")
            return data
        print(f"Transient DEX dependency failure; retry {attempt + 2}/{MAX_ATTEMPTS} after {delay:.0f}s",
              flush=True)
        time.sleep(delay)


def cache_dependency(path, data):
    CACHE.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=CACHE, prefix=path.name + ".", suffix=".partial",
                                         delete=False) as out:
            temporary = Path(out.name)
            out.write(data)
        if path.is_symlink():
            raise RuntimeError("Unsafe DEX dependency cache entry")
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def dependencies(download=False):
    jars = []
    for item in json.loads((TOOLS / 'dependencies.json').read_text(encoding='utf-8')):
        path = CACHE / item['url'].rsplit('/', 1)[1]
        if path.is_symlink():
            raise RuntimeError('Unsafe DEX dependency cache entry: ' + path.name)
        if not path.is_file():
            if not download:
                raise RuntimeError('Missing pinned DEX build dependency: ' + path.name)
            cache_dependency(path, download_dependency(item))
        if path.is_symlink() or sha256(path) != item['sha256']:
            raise RuntimeError('DEX build dependency checksum mismatch: ' + path.name)
        jars.append(path)
    return jars


def rewrite(source, work, *, download=False):
    """Return replacement DEX paths only after all twelve exact targets validate.

    Caller owns packaging, bootstrap selection and final ART verification. Never
    modifies the input APK. Missing or changed descriptors are a packaging error.
    """
    source, work = Path(source).resolve(strict=True), Path(work).resolve()
    if work.exists():
        raise ValueError('DEX rewrite work directory must be new')
    input_hash = sha256(source)
    jars = dependencies(download)
    work.mkdir(parents=True)
    classes = work / 'tool-classes'
    classes.mkdir()
    classpath = os.pathsep.join(map(str, jars))
    tool = TOOLS / 'BridgeRewriter.java'
    subprocess.run(['javac', '-encoding', 'UTF-8', '-cp', classpath, '-d', str(classes), str(tool)], check=True, timeout=90)
    output = work / 'rewritten'
    subprocess.run(['java', '-cp', classpath + os.pathsep + str(classes), 'BridgeRewriter', str(source), str(output)], check=True, timeout=180)
    targets = (output / 'bridges.tsv').read_text(encoding='utf-8').splitlines()
    if len(targets) != 12 or len(set(targets)) != 12:
        raise RuntimeError('Incomplete DEX rewrite receipt')
    locations = (output / 'locations.tsv').read_text(encoding='utf-8').splitlines()
    location_counts = {}
    for row in locations:
        columns = row.split('\t')
        if columns[0] == '#count':
            if len(columns) != 3 or columns[1] in location_counts:
                raise RuntimeError('Invalid Location rewrite counts')
            location_counts[columns[1]] = int(columns[2])
        elif len(columns) != 8 or columns[0] not in ('rewritten', 'ignored-owner', 'ignored-descriptor'):
            raise RuntimeError('Invalid Location rewrite inventory')
    if set(location_counts) != {'rewritten', 'ignored', 'unsupported'} or location_counts['unsupported']:
        raise RuntimeError('Incomplete Location rewrite inventory')
    if any(value < 0 for value in location_counts.values()) or sum(row.startswith('rewritten\t') for row in locations) != location_counts['rewritten'] or sum(row.startswith(('ignored-owner\t', 'ignored-descriptor\t')) for row in locations) != location_counts['ignored']:
        raise RuntimeError('Location rewrite count mismatch')
    result = {p.name: p for p in output.glob('classes*.dex')}
    if not result:
        raise RuntimeError('DEX rewrite produced no output')
    with zipfile.ZipFile(source) as archive:
        if len(set(archive.namelist())) != len(archive.namelist()):
            raise ValueError('Duplicate input APK members')
        for name, path in result.items():
            if name not in archive.namelist() or not path.read_bytes().startswith(b'dex\n'):
                raise RuntimeError('Invalid DEX replacement')
    if sha256(source) != input_hash:
        raise RuntimeError('Input APK changed during rewrite')
    receipt = {'input_sha256': input_hash, 'rewriter_sha256': sha256(tool),
               'dependencies': {p.name: sha256(p) for p in jars}, 'targets': targets,
               'dex_sha256': {n: sha256(p) for n, p in result.items()},
               'runtime_verified': False, 'location_counts': location_counts,
               'location_inventory_sha256': sha256(output / 'locations.tsv'),
               'location_offset_units': 'source DEX code units',
               'location_callsites': [row for row in locations if not row.startswith('#count\t')]}
    (work / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    return result, receipt
