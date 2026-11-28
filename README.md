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
| Latest public release | **PGS v0.0.6** |
| Status | **In-app update from v0.0.5, installation and startup confirmed by owner screenshots; first-audit follow-up accepted by the owner** |
| Reference candidate | [PGS v0.0.2](https://github.com/LucianoToscano/PGS/releases/tag/untagged-268fa715660bc21061a4) |
| Base game | Pokémon GO **0.439.0** |
| Installed app name | **Pokémon GO** |
| Android package | `com.nianticlabs.pokemongo` |

The PGS project version is distinct from the base game's version. The latest public release is offered by the in-app updater.

## Download and install

1. Open the [PGS v0.0.6 release](https://github.com/LucianoToscano/PGS/releases/tag/v0.0.6).
2. Download `PGS.v0.0.6.apk` and compare its SHA-256 with `SHA256SUMS.txt`: `e69ed234a34a106052343ba59b2ea62d1158a8ed72326f82e892ba5479d0ca4e`.
3. Review the attached `build-info.json` and `PGS.json`. Owner screenshots confirm the in-app upgrade from v0.0.5, successful startup and retained session/settings. Google sign-in and other features were accepted by the owner, without separate detailed test logs.
4. For Root, the same release includes `PGS-Root.apk`, `PGS-Root-module.zip` and `root-build-info.json`. Check the assets against `SHA256SUMS.txt` and read the [Root guide](docs/ROOTED.md). Root packaging passed automated checks; device tests were accepted by the owner, not independently documented.

Do not mistake source archives or preview-only packages for a complete APK. Original build inputs must remain private.

## Project automation

- [PGS AUTO BUILD](docs/PGS_AUTO_BUILD.md) — authorized signed candidates only.
- [PGS AUTO BACKUP](docs/PGS_AUTO_BACKUP.md) — source snapshots and checksums.
- [PGS AUTO SYNC](docs/PGS_AUTO_SYNC.md) — read-only upstream revision monitoring.

## Website and guides

- [PGS website](https://lucianotoscano.github.io/PGS/)
- [Feature guides](https://lucianotoscano.github.io/PGS/?guide=all)
- [Website workflow](https://github.com/LucianoToscano/PGS/actions/workflows/pages.yml)
- [Source checks](https://github.com/LucianoToscano/PGS/actions/workflows/ci.yml)

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

Existing code, native libraries, Java/JNI symbols, saved-setting keys, and provenance records remain intact for update compatibility. Historical records should not be confused with current PGS releases.

## Community

**Discord:** https://discord.gg/SdwU4VnfW

**GitHub:** https://github.com/LucianoToscano/PGS

**Website:** https://lucianotoscano.github.io/PGS/

The Website workflow has successfully built and deployed through GitHub Pages; this does not change the installed Android application. This documentation change does not alter the in-game menu artwork or joystick.

## License

PGS contributions and inherited MIT-licensed source are available under the [MIT License](LICENSE). Copyright and permission notices are retained in [NOTICE](NOTICE) and LICENSE. [Third-party notices](THIRD_PARTY.md) and [additional license information](THIRD_PARTY_LICENSES.md) identify separate component terms. Pokémon GO and its assets are not covered by this license. PGS is an independent project and is not affiliated with the game publisher.
