# PGS — Update continuity and signing policy

[🇺🇸 English](PGS_UPDATE_POLICY.md) · [🇧🇷 Português (Brasil)](../pt-BR/PGS_UPDATE_POLICY.md)

PGS does **not** change the Android application ID. The distribution file is named `PGS.apk` internally, but the installed package and label remain `com.nianticlabs.pokemongo` and **Pokémon GO**. Do not modify other independently installed applications.

## Permanent PGS certificate

PGS certificate SHA-256:

`D9:5C:6B:DF:CB:D9:1D:C5:C9:CD:E6:98:48:7C:88:E4:99:47:71:A4:75:E4:EF:DE:45:67:B8:D5:F4:4E:96:CF`

This certificate must never change. Signing secrets belong in GitHub Actions and **not** in the source repository. Do not generate a new JKS for future PGS updates. The build fails if the final certificate does not match.

## Android versions

| PGS version | Base game | Android `versionCode` |
|---|---|---:|
| v0.3.8-pgs.2 | Pokémon GO 0.439.0 | 2026111602 |
| v0.3.8-pgs.3 | Pokémon GO 0.439.0 | 2026111603 |
| **v0.0.1** | Pokémon GO 0.439.0 | **2026111604** |
| **v0.0.2 (candidate)** | Pokémon GO 0.439.0 | **2026111605** |

The latest verified PGS code is tracked in [`pgs/PGS_LAST_VERSION_CODE`](../../pgs/PGS_LAST_VERSION_CODE). For each full release, `pgs/release_apk.py` uses `max(game_code, previous_pgs_code+1)` before signing the non-root APK. The original `game_version_code` is retained for Root-module compatibility checks. The actual signed code is recorded in `build-info.json` as `apk_version_code`.

**After completing and verifying each signed APK**, record its `apk_version_code` in `PGS_LAST_VERSION_CODE` before the next build. The targeted update tool `pgs/pgs_update.py` also validates the source APK, signing certificate, package, manifest-only changes, and output signature.

## Verification before distribution

1. Confirm `packageName=com.nianticlabs.pokemongo`, the permanent PGS certificate, and a `versionCode` strictly higher than the version to be replaced.
2. Verify the certificate with `apksigner verify --print-certs`, ZIP integrity, and alignment using `zipalign`.
3. Preserve user data; **never recommend uninstalling** as the normal update procedure.
4. Confirm installation and sign-in on a real device. Successful compilation alone does **not** demonstrate a working game.

PGS `v0.3.8-pgs.3` was built and signed in [Actions #45963966748](https://github.com/LucianoToscano/PGS/actions/runs/45963966748) with SHA-256 `1e42c50f84afe5edf9570dfa808ba5e4be99b64d3ae28199b7316981c7414d4c`. It was not physically tested on the user's phone.

## Protecting the full-release path

The PGS ledger `PGS_LAST_VERSION_CODE` distinguishes PGS output from a legacy build. `pgs/release_apk.py` requires `PGS_KEYSTORE` to reference **the existing PGS key**, names its internal output `PGS.apk`, and rejects output unless its certificate fingerprint matches the permanent PGS certificate. The build is blocked if the ledger is missing.

The upstream publication workflow and historical PGS rebuild workflows are now explicitly disabled on current sources. Their original implementations and build records remain in Git history. The previously signed packages are not modified.

Tests cover missing signing keys, invalid `versionCode`, and unrecognized signing certificates. **They do not replace full-APK verification or physical installation.**

## Independent PGS public versioning

The independent release line began at `v0.0.1`. The requested artifact filename is `PGS v0.0.1.apk`, while safe internal generation continues to use `PGS.apk` until it is verified and copied to the release asset.

The first candidate advanced from Android `versionCode=2026111603` to `2026111604`; the current `v0.0.2` candidate uses **2026111605**. The visible PGS project version is separate from Pokémon GO's base `0.439.0` and is not an Android version code.

Starting with `v0.0.1`, the updater queries **only** the `LucianoToscano/PGS` release feed, checks the versioned asset and its SHA-256, then delegates installation to Android. Already installed old packages cannot gain the new updater retroactively: the first migration to this line requires manually installing the compatible PGS APK over the previous installation.

Without real-device evidence, any successful build remains a **candidate or draft**, not a confirmed working gameplay release.

## GitHub asset filenames

Actions artifacts contain `PGS v0.0.1.apk` or `PGS v0.0.2.apk`. GitHub normalizes spaces to dots in release asset names: `PGS.v0.0.1.apk` and `PGS.v0.0.2.apk`. The PGS updater checks the exact normalized filename and SHA-256. This has no effect on Android package identity or signing.

The candidate `v0.0.1` was signed with `versionCode=2026111604`; `v0.0.2` uses **2026111605**. The next complete APK must use **2026111606 or higher**. Recording a version code in the ledger does not prove that physical installation was tested.

The releases remain **drafts** until actual sign-in and installation checks pass. The automated archive comparison preserves native libraries and all other game DEX files, excluding only the updated PGS control DEX and manifest `versionCode`.

## v0.0.2 — Branding built into the APK

The `v0.0.2` rebuild uses only the fully signed `v0.0.1` APK with verified source SHA-256 `23c0c4e9f9e87676038856e76b16613c91bf4bbd04a5c8cc9eb4f317d6926ef4` ([Actions #45973576985](https://github.com/LucianoToscano/PGS/actions/runs/45973576985)). It updates the PGS control DEX and internal displayed version, but compares the hashes of all other game entries. No automatic APKMirror download is involved.

The historical v0.0.2 build produced a complete signed APK and verification receipts with the permanent PGS signer, package `com.nianticlabs.pokemongo`, and game version `0.439.0`. The existing release remains a draft. Its verified run is https://github.com/LucianoToscano/PGS/actions/runs/45980315394; the Actions artifact is subject to expiration.

The original in-game icon and joystick are untouched. The previous project's Ko-fi sponsorship link was removed without substituting an unauthorized account.

## Current full-candidate path

All four historical publication/rebuild workflows are inert, read-only refusals. To validate the next full candidate, use [PGS v0.0.3 candidate validation](https://github.com/LucianoToscano/PGS/actions/workflows/pgs-v0.0.3-candidate.yml), select `main`, and confirm `authorized_input` only if you are authorized to use the configured hash-pinned game input and existing signer. The run uploads receipts only, not a downloadable APK or a public release. The bundle verifier expects PGS artifact names by default; archived bundles require explicit `--legacy-names`. The installed package, signer and release ledger are unchanged.

### Required private configuration

The v0.0.3 validation run [46047731065](https://github.com/LucianoToscano/PGS/actions/runs/46047731065) passed its source checks but stopped because `PGS_INPUT_URL` was empty. An early configuration check now reports missing setting names before tool installation. It never prints secret values or writes a signing key. Existing signing aliases remain accepted. Set the repository Actions secret `PGS_INPUT_URL` to an authorized HTTPS location for the exact original game input selected in `pgs/native/schema/game/current.json` (0.439.0). Expected input SHA-256: `c6d3c04c38ca2f2446957633b4fee8c93dcc9cebdbbaddc9cb9651722ef8f54f`. Do not substitute a previously modified APK, change the hash to accept another file, or commit the URL/credentials. The existing signer is unchanged. The maintainer must supply this authorized input; an empty value cannot be repaired by a source change.

The standalone test-only preview now uses `dev.pgs.preview`. It is a separate Android installation from the previous preview package; old preview data is not automatically migrated and the original package is not uninstalled. The actual game and Root installer package identities are unchanged. The build cleanup still recognizes historic preview receipts. Feed configuration examples use the new PGS path for new deployments; the production endpoint is unchanged until independently verified.
