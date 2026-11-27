# PGS — Building, signing, and installing

[🇺🇸 English](BUILDING.md) · [🇧🇷 Português (Brasil)](../pt-BR/BUILDING.md)

This guide applies only to **PGS — Pokémon GO Spoofers** installers. Some technical interfaces retain legacy names for compatibility; public releases belong exclusively to https://github.com/LucianoToscano/PGS.

## Current candidate

| Field | Value |
|---|---|
| PGS | **v0.0.2** (candidate) |
| Base game | Pokémon GO `0.439.0` (ARM64) |
| Installed app name | **Pokémon GO** |
| Android package | `com.nianticlabs.pokemongo` |
| Android `versionCode` | `2026111605` |
| Signing certificate SHA-256 | `D9:5C:6B:DF:CB:D9:1D:C5:C9:CD:E6:98:48:7C:88:E4:99:47:71:A4:75:E4:EF:DE:45:67:B8:D5:F4:4E:96:CF` |
| Distribution APK | `PGS v0.0.2.apk` |
| Release asset name | `PGS.v0.0.2.apk` |
| APK SHA-256 | `91865f6242519091a771617f962f17620405624a4a56addec0909d2cdf6b68c1` |

**Release workflow:** https://github.com/LucianoToscano/PGS/actions/workflows/pgs-v0.0.2-release.yml

**Verified full build:** https://github.com/LucianoToscano/PGS/actions/runs/45980315394

Do not mistake a source ZIP or a preview APK for the complete game.

## Source checks

Run in a configured development environment:

```sh
python -B tools/check.py
```

CI also runs Linux native checks and builds Android controls in GitHub Actions. Language catalogs, update rules, signing policy, and behavioral regressions are included in the automated tests.

## Compiling controls

The source directory name remains compatible with the existing installed runtime. To compile the Android controls:

```sh
python -B pgs/build.py
```

A compatible JDK and Android SDK are required. The resulting preview is **not** a complete game installer. Only the dedicated full-release workflow combines compiled controls with an approved base APK, hashes all original entries, and signs the complete APK.

## Permanent signing certificate

**Always use the existing PGS signing key.** Never generate a replacement JKS for a distributed APK, and never expose GitHub Secrets, private keys, or passwords.

The workflow uses the already configured PGS signing Secrets and validates the final certificate, unchanged package name, and increasing `versionCode`. A developer-key-signed preview must not be distributed as a working release.

See the full [PGS update policy](PGS_UPDATE_POLICY.md). The next APK after `v0.0.2` must use `versionCode` **2026111606 or higher**.

## Safe release process

1. Make focused changes in a branch and run automated tests.
2. Build the **complete APK** using the dedicated PGS workflow.
3. Check `PGS.json`, `SHA256SUMS.txt`, APK size, certificate, package, and base game version.
4. Prepare a **draft GitHub Release**; publish only after installation and sign-in are confirmed on a real device.
5. Test updating **over** an existing compatible PGS installation without uninstalling it or losing data.

The in-app updater checks only releases in the PGS repository. On GitHub, it expects the normalized asset name `PGS.vX.Y.Z.apk` and verifies the corresponding SHA-256 before handing off to Android's installer.

## Compatibility

The Android package stays `com.nianticlabs.pokemongo`, the installed name remains **Pokémon GO**, and the signing certificate must be identical. Native libraries, Java/JNI bindings, and existing saved preferences may only be renamed through a separately tested migration.

The in-game menu artwork and joystick are unchanged at this stage. No other installed applications should be modified.

**A successfully compiled and signed APK does not prove real-device installation, sign-in, or gameplay.**

### Authorized input in the existing repository

Use the existing PGBR-style release-asset model in PGS: create an **unpublished draft** with tag `build-inputs`, and only if authorized to store the original game package, attach `Pokemon_GO_0.439.0_ARM64_ORIGINAL.apkm` (169083658 bytes, SHA-256 `c6d3c04c38ca2f2446957633b4fee8c93dcc9cebdbbaddc9cb9651722ef8f54f`). Never publish that draft. A draft in a public repository is not equivalent to a private repository. If the storage authorization requires a genuinely private location, use an approved private storage arrangement instead; do not upload here. The manual candidate job uses its ephemeral repository token and `tools/pgs_pinned_input.py` to check the exact draft, asset state, size, digest and downloaded archive hash, then recheck the draft. Only this job needs `contents: write` for draft visibility; this permission applies to the whole job, not just a step. Checkout does not persist credentials. The script never modifies a release, downloads from another repository, publishes or uploads game files. `PGS_INPUT_URL` and external input tokens are no longer required by the candidate workflow. The existing signing aliases are retained; the key is loaded only after archive verification, and the workflow uploads verification receipts only by default. The maintainer must create the draft and supply the authorized archive. Source checks and the version monitor remain read-only except the monitor's existing issue notification job. The monitor does not download game packages, promote profiles or trigger signed builds automatically.

### Optional authorized candidate retention

The first full v0.0.3 build (Actions run 46054404520, source d4eb3192c505ea53e8c072cefc1703f604c21122) passed static validation with APK SHA-256 `e9cae313bd3d98087ed370e211c690857c2acb18973f740faf1c814d86dda225`, 185818917 bytes, versionCode 2026111606 and the existing signer. Its temporary APK was deleted; only the two receipts were retained. Device and in-place update tests remain pending.

The workflow still defaults to receipt-only validation. If the maintainer has authorization to retain the signed modified candidate in this unpublished GitHub draft, explicitly select both `authorized_input` and `retain_authorized_candidate` on main. The optional retention step rebuilds and independently verifies the APK, removes the temporary key, and creates a new unpublished `v0.0.3` draft containing only `PGS.v0.0.3.apk`, `PGS.json`, `build-info.json` and `SHA256SUMS.txt`. It checks the uploaded digests and source commit; it never uploads the original APKM, modifies `build-inputs`, overwrites a candidate, publishes a release or advances the installed-version ledger. A partial or conflicting draft requires maintainer review; do not publish it. The new APK hash may differ from the historical validation run. The signed candidate is not device tested or approved for distribution. A draft in a public repository is not a private repository; use approved private storage instead if required by the applicable authorization. No downloadable APK is exposed via public Actions artifacts.

### Transient build dependency availability

The candidate attempt 46057849390 stopped on HTTP 429 while downloading a pinned DEX build-tool JAR from Maven Central, before compiling the APK. The downloader now uses at most four attempts for transient HTTP failures and timeouts, respects bounded Retry-After delays, and checks the existing SHA-256 pins before writing any cache entry. No dependency version, source URL, or hash has changed. Permanent HTTP/TLS errors, oversized responses and checksum mismatches still fail closed. The cache contains build tooling only, never the original game package or signing key.
