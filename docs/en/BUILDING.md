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
