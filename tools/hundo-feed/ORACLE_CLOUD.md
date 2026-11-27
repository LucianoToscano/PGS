# PGS Hundo Feed — Oracle Cloud deployment

Deploy the existing Python collector on an OCI Always Free Linux VM. This is a deployment runbook, not a record of an existing server. Keep the APK endpoint unchanged until the new endpoint passes verification.

## 1. OCI setup (owner action)

- Create or sign in to an Oracle Cloud account using https://www.oracle.com/br/cloud/free/. Choose the home region carefully; use Brazil East (São Paulo) if offered and appropriate.
- Create one Compute instance named `pgs-hundo-server`, using Ubuntu 24.04 LTS on `VM.Standard.A1.Flex`, 1 OCPU, 4 GB RAM, and a 50 GB boot volume. Verify Always Free eligibility and current limits in the console before creating any resource. Do not upgrade to a paid account or provision paid resources without explicit approval. Capacity and continued availability are not guaranteed; idle instances may be reclaimed.
- Use a public subnet with internet access and a public IPv4 address. Permit inbound TCP 443 and, for HTTP certificate validation/redirects, TCP 80. Restrict TCP 22 to the administrator's public IP/CIDR; retain the SSH private key locally. Configure both OCI network rules and the VM firewall. Do not expose application or database ports.
- Point a DNS name controlled by PGS to the public IP. Obtain HTTPS via Let's Encrypt or another trusted CA. The final feed URL is `https://<your-domain>/feed/hundos.json`. Do not claim a domain or endpoint before it is configured and verified.

Official OCI Always Free documentation: https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm

## 2. Install the collector

Connect over SSH with the account and private key created in the console. After the feed PR is merged, clone the PGS repository and check out the approved commit. Review source before executing.

```sh
sudo apt-get update
sudo apt-get install -y python3 git nginx certbot python3-certbot-nginx
git clone https://github.com/LucianoToscano/PGS.git
cd PGS
# Check out the reviewed, merged feed commit before installation.
python3 -B -m unittest discover -s tools/hundo-feed -p 'test_*.py'
sudo useradd --system --no-create-home --shell /usr/sbin/nologin hundofeed
sudo install -d -o root -g root -m 0755 /opt/hundo-feed
sudo install -d -o hundofeed -g hundofeed -m 0755 /var/www/pgs/feed
sudo install -o root -g root -m 0644 tools/hundo-feed/hundo_feed.py /opt/hundo-feed/hundo_feed.py
sudo install -o root -g root -m 0644 tools/hundo-feed/hundo-feed.service /etc/systemd/system/hundo-feed.service
sudo install -o root -g root -m 0600 tools/hundo-feed/hundo-feed.env.example /etc/hundo-feed.env
sudoedit /etc/hundo-feed.env
```

For an existing installation, do not recreate the user or overwrite the live environment file. Back up the existing config with root-only permissions before upgrading.

## 3. Configure approved sources

Enable only sources for which the operator has permission to collect and redistribute data. The existing client reads FaustusFoundry at `/pgrazor/hundos.json`; the proposed `/pgs/hundos.json` endpoint has not been verified. Client access does not by itself establish permission to republish.

For a first authorized published-source-only deployment, use the following environment settings (replace the example URL with the verified authorized endpoint):

```ini
HUNDO_SOURCES=published
PGS_UPSTREAM_FEED_URL=https://feed.faustusfoundry.com/pgs/hundos.json
PGS_UPSTREAM_FEED_INTERVAL=60
HUNDO_OUT=/var/www/pgs/feed/hundos.json
```

This is an example, not a working or confirmed source. Do not enable it until verified and authorized. Add `citymaps`, `pogocoordinates` or `livepokemap` only after confirming access and redistribution rights. Configure the relevant account credentials and rate limits in the root-only environment file, not in GitHub, the public feed, or the APK. Do not use the new PGS public feed as its own upstream.

To validate configuration without publishing a placeholder, run the collector as its service user with a separate output under a private temporary directory. Load the trusted environment file as root, and ensure it contains shell-compatible assignments before sourcing it. Inspect the JSON for current timestamps, valid coordinates and source statuses. Then start the production service:

```sh
sudo systemctl daemon-reload
sudo systemctl enable --now hundo-feed
sudo systemctl status hundo-feed
sudo journalctl -u hundo-feed -n 30 --no-pager
```

## 4. Publish only the feed over HTTPS

Create a dedicated Nginx server block (replace `feed.example.org` with the actual DNS name). Do not expose the environment, collector source, state, or logs.

```nginx
server {
    listen 80;
    server_name feed.example.org;

    location = /feed/hundos.json {
        alias /var/www/pgs/feed/hundos.json;
        default_type application/json;
        add_header Cache-Control "public, max-age=15, must-revalidate" always;
        limit_except GET { deny all; }
    }

    location / { return 404; }
}
```

Enable the server block, check with `sudo nginx -t`, reload Nginx, and run `sudo certbot --nginx -d feed.example.org` once DNS and port 80 work. Enable HTTP-to-HTTPS redirection. Confirm certificate renewal and ensure the feed is available via trusted HTTPS. Only public compact JSON should be accessible. Use rate limiting and caching consistent with expected traffic; avoid collecting unnecessary personal data in access logs.

## 5. Cutover gate

- Verify HTTP 200, JSON schema v1, exact coordinates, recent `fetched_ms`, valid unexpired encounters and spots, and nonempty results when the sources have active spawns.
- Observe several successful publication cycles and confirm the collector recovers from an unavailable source. Compare coverage with the currently used authorized feed; no identical-count guarantee.
- Verify the service restarts after reboot and monitor actual OCI usage, storage, network and service errors. Maintain a backup and restoration procedure; Always Free instances are not an availability guarantee.
- Only after validation, update the URL in `pgs/src/dev/pgs/ShundoSniper.java`, run the full source/build checks, generate a signed candidate, and verify the new feed on a real device. Keep the previous APK for rollback.

No credentials, live feed payloads, or domain ownership are supplied by this document.
