"""Fetch the private, pinned game input and decode the CI signing key without logging secrets."""
import base64
import os
import re
from pathlib import Path
import urllib.parse
import urllib.request
from game_update import current_profile, verify_input
ROOT = Path(__file__).resolve().parents[1]/'pgs'
class HttpsRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urllib.parse.urlsplit(newurl).scheme != 'https': raise ValueError('Insecure redirect')
        redirected=super().redirect_request(req,fp,code,msg,headers,newurl)
        if redirected and urllib.parse.urlsplit(req.full_url).netloc != urllib.parse.urlsplit(newurl).netloc:
            redirected.remove_header('Authorization')
        return redirected

def required_setting(name):
    value = os.environ.get('PGS_' + name) or os.environ.get('PGRAZOR_' + name)
    if not value:
        raise SystemExit('Required PGS input/signing setting is missing: ' + name)
    return value

def input_headers(url):
    """Send a repository-scoped credential only to an exact GitHub asset API URL."""
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != 'https':
        raise SystemExit('Input URL must use HTTPS')
    scoped_token = os.environ.get('PGS_INPUT_TOKEN')
    if parsed.hostname == 'api.github.com':
        if (parsed.netloc.lower() != 'api.github.com' or parsed.query or parsed.fragment
                or not re.fullmatch(r'/repos/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/releases/assets/[0-9]+', parsed.path)):
            raise SystemExit('Use an exact GitHub release-asset API URL')
        token = scoped_token or os.environ.get('GITHUB_TOKEN')
        if not token:
            raise SystemExit('GitHub asset access requires an authorized repository token')
        return {'Accept': 'application/octet-stream', 'Authorization': 'Bearer ' + token}
    if scoped_token:
        raise SystemExit('PGS_INPUT_TOKEN is only for GitHub release assets')
    return {}


def main():
    url=required_setting('INPUT_URL')
    headers=input_headers(url)
    folder=ROOT/'input';folder.mkdir(exist_ok=True)
    output=folder/'game.apkm'
    opener=urllib.request.build_opener(HttpsRedirect())
    try:
        with opener.open(urllib.request.Request(url,headers=headers),timeout=90) as source,output.open('wb') as dest:
            if urllib.parse.urlsplit(source.url).scheme!='https': raise ValueError('Insecure redirect')
            total=0
            while chunk:=source.read(1024*1024):
                total+=len(chunk)
                if total>2_000_000_000: raise ValueError('Input too large')
                dest.write(chunk)
    except Exception: raise SystemExit('Private game input download failed; check the secret URL') from None
    verify_input(output, current_profile())
    key=Path(required_setting('KEYSTORE'));key.parent.mkdir(parents=True,exist_ok=True)
    key.write_bytes(base64.b64decode(required_setting('KEYSTORE_BASE64'),validate=True))
if __name__=='__main__': main()
