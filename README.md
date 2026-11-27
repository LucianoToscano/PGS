<p align="center">
  <img src="website/public/pgs-full.png" width="360" alt="PGS — Pokémon GO Spoofers">
</p>

<h1 align="center">PGS</h1>
<h3 align="center">Pokémon GO Spoofers</h3>

<p align="center">An independent Android project with location controls, a joystick, maps, and companion tools for Pokémon GO.</p>

<p align="center">
  <a href="https://github.com/LucianoToscano/PGS/actions">Builds</a> ·
  <a href="https://github.com/LucianoToscano/PGS/releases">Releases</a> ·
  <a href="https://discord.gg/SdwU4VnfW">PGS Discord</a> ·
  <a href="https://lucianotoscano.github.io/PGS/">Website</a>
</p>

<p align="center">
  <strong>🌐 Languages:</strong>
  <strong>🇺🇸 English</strong> ·
  <a href="README.pt-BR.md">🇧🇷 Português (Brasil)</a>
</p>

## Current PGS version

| Property | Value |
|---|---|
| PGS release line | **PGS v0.0.2** |
| Base game | Pokémon GO **0.439.0** |
| Installed app name | **Pokémon GO** |
| Android package | `com.nianticlabs.pokemongo` |
| Android `versionCode` | `2026111605` |
| Signing | **Existing permanent PGS certificate, unchanged** |
| Status | **Full APK compiled and verified; physical device testing pending** |

**PGS v0.0.2** is a draft release candidate, not a published stable release. The PGS project version is distinct from the base game's version. Android `versionCode` must increase with each new APK so that supported existing PGS installations can be updated in place.

## Download and install

1. Open the [verified PGS v0.0.2 full build](https://github.com/LucianoToscano/PGS/actions/runs/45980315394).
2. Under **Artifacts**, download `PGS-v0.0.2`, extract the ZIP and find **`PGS v0.0.2.apk`**.
3. Check `SHA256SUMS.txt`. The candidate APK's expected SHA-256 is `91865f6242519091a771617f962f17620405624a4a56addec0909d2cdf6b68c1`.
4. To update an existing, compatible PGS installation, install **without first uninstalling it**. The Android package and signing certificate must match to preserve app data.
5. Check startup, sign-in, displayed version, menu, Discord link, and saved settings on the device. These **real-device checks remain unconfirmed**.

The GitHub Actions artifact uses `PGS v0.0.2.apk`. GitHub normalizes spaces in release-asset names, resulting in `PGS.v0.0.2.apk` on the draft Release. The release **has not been published as stable**.

Do not mistake source archives or preview-only packages for the full game APK.

The full **PGS v0.0.3** signed candidate is retained in an unpublished draft; device testing remains pending. The full **PGS v0.0.4** candidate has its own validation run. Subsequent signed candidates use the permanent request-scoped build workflow. Maintainers can use the [authorized candidate validation workflow](https://github.com/LucianoToscano/PGS/actions/workflows/pgs-build.yml) for receipt-only validation. The v0.0.2 link above is an existing historical build run, not an instruction to rebuild it. Actions artifacts can expire.

## Features

- Location controls, joystick, coordinates, maps, GPX routes, and cooldown estimates.
- Session statistics, encounter counter, IV display, catching, and transfer options.
- PokéStop, item, gift, buddy, and battle helpers.
- Pokémon maps and feeds, optional automation, and navigation utilities.
- Settings search, light/dark themes, saved preferences, and **12 language choices** (system + 11 languages).

Experimental features depend on the game's version and environment. They do not guarantee server-side outcomes or freedom from account restrictions.

## Documentation

| Topic | 🇺🇸 English | 🇧🇷 Português (Brasil) |
|---|---|---|
| Build and verify | [Build guide](docs/en/BUILDING.md) | [Compilação](docs/pt-BR/BUILDING.md) |
| Update and signing policy | [Updates](docs/en/PGS_UPDATE_POLICY.md) | [Atualizações](docs/pt-BR/PGS_UPDATE_POLICY.md) |
| In-app languages | [Languages](docs/en/PGS_LANGUAGES.md) | [Idiomas](docs/pt-BR/PGS_LANGUAGES.md) |
| Contribution guide | [Contributing](CONTRIBUTING.md) | [Como contribuir](CONTRIBUTING.pt-BR.md) |
| Release history | [Changelog](CHANGELOG.md) | [Registro de alterações](CHANGELOG.pt-BR.md) |
| GitHub and Website workflow | [Repository settings](docs/en/PGS_REPOSITORY_SETTINGS.md) | [Configurações do repositório](docs/pt-BR/PGS_REPOSITORY_SETTINGS.md) |

More technical references: [Architecture](docs/ARCHITECTURE.md), [community improvements](docs/PGS_COMMUNITY_REVIEW.md), [official artwork](docs/PGS_OFFICIAL_LOGOS.md), and [repository/Pages setup](docs/PGS_REPOSITORY_SETTINGS.md). These additional technical references are not all translated yet; their language is indicated by the document itself.

The current source uses PGS names for its own Java/JNI classes, native libraries, private C/C++ interfaces and generated assets. Installed storage keys, selected public compatibility contracts and provenance are retained where changing them could break older installations. Historical records are not current PGS releases.

## Community

**Discord:** https://discord.gg/SdwU4VnfW

**GitHub:** https://github.com/LucianoToscano/PGS

**Website:** https://lucianotoscano.github.io/PGS/

The Website workflow has successfully built and deployed through GitHub Pages; this does not change the installed Android application. This documentation change does not alter the in-game menu artwork or joystick.

## License

PGS contributors' original contributions are licensed under the [MIT License](LICENSE), with the original copyright and permission notices retained. See [NOTICE](NOTICE) for attribution and [third-party licenses](THIRD_PARTY_LICENSES.md) for exclusions and dependency notices. PGS is an independent project and is not affiliated with the game publisher.

Original PGRazor source is available under the MIT License. Third-party components retain their own licenses. Pokémon GO and its assets are not covered by this license. PGRazor is an independent project and is not affiliated with the game publisher.
