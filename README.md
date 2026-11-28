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
| Latest stable release | **PGS v0.0.5** |
| Status | **Installation and app opening confirmed by the project owner on a physical device; Google sign-in and in-app update not separately verified** |
| Reference candidate | [PGS v0.0.2](https://github.com/LucianoToscano/PGS/releases/tag/untagged-268fa715660bc21061a4) |
| Base game | Pokémon GO **0.439.0** |
| Installed app name | **Pokémon GO** |
| Android package | `com.nianticlabs.pokemongo` |

The PGS project version is distinct from the base game's version. The stable release is offered by the in-app updater.

## Download and install

1. Open the [PGS v0.0.5 release](https://github.com/LucianoToscano/PGS/releases/tag/v0.0.5).
2. Download `PGS.v0.0.5.apk` and compare its SHA-256 with `SHA256SUMS.txt`: `fa139a05d884ae2c487f8af68673c049d7db03eaae8fca8efecc88f6cf2c4ea9`.
3. Review the attached `build-info.json` and `PGS.json`. Installation and app opening were confirmed by the project owner. Google sign-in, saved settings, gameplay and in-app update remain to be verified independently.

Do not mistake source archives or preview-only packages for a complete APK. Original build inputs must remain private.

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
