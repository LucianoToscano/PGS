<p align="center"><img src="pgs/branding/pgs.svg" width="88" alt="PGS emblem (upstream drawing retained)"></p>
<h1 align="center">PGS — Pokémon GO Spoofers</h1>
<p align="center">A compact Android interface for location controls and Pokémon GO automation.</p>

PGS, an independent derivative of MIT-licensed upstream code (see [NOTICE](NOTICE)), adds an in-game menu, an independent joystick, encounter controls, and optional automation to Pokémon GO. Settings persist across restarts, with light and dark themes.

## PGS community integration

PGS retains the inherited source and its MIT and third-party notices. Its active source, internal package names, asset paths and interface identity use the PGS name. Device-level migration of saved settings remains to be verified.

The current candidate adds the joystick direction lock, a direct gift shortcut, configurable LivePokeMap refresh, populated wild-encounter IVs for VGP+, owned-IV refresh/layer fixes, real-GPS readiness, buddy timeout recovery and the Silver Pinap preference migration. Android packaging also works on Linux with the pinned toolchain.

- Hold the joystick centre for **1.5 seconds**, drag and release to lock direction; hold the padlock for **0.5 seconds** to stop. Leaving the map or losing the camera releases it.
- Open **Quick Menu → Send & Open Gifts** for the existing batch dialog; press Start there when ready.
- In **Shundo Sniper**, choose **LivePokeMap refresh**. The default is five minutes; server limits can require a longer wait. The feed's **Global** view refreshes manually.
- See [the PGS integration review](docs/PGS_COMMUNITY_REVIEW.md) for source attribution, what was already present, remaining proposals and validation limits.

PGS candidate artifacts are produced in [this repository's Actions](https://github.com/LucianoToscano/PGS/actions). Upstream download links are not PGS updates. Compilation and automated fixtures do not establish Android installation or gameplay results; those observations are recorded separately.

The settings panel is grouped into Play, Automation and App cards, with an instant search field at the top. Search matches names, descriptions, categories and common synonyms (for example "fake gps" or "light mode"), and tapping a result opens the page, expands any collapsed section, and scrolls straight to that row.

## PGS interface languages

Open **Settings → Display & Performance → Language → PGS language**, choose a language, then fully close and reopen the game. The choices are **System, Deutsch, English, Español, Français, Português, Русский, Italiano, 繁體中文, Nederlands, ภาษาไทย and 한국어**. The selected language is shared by all accounts and included in explicit settings backups. The interface keeps its current language until the process restarts.

Translations are bundled offline. Search accepts both the selected language and the original English setting names. System follows the device language, using English if it is unsupported; Portuguese uses the Brazilian catalog and Chinese uses the Traditional Chinese catalog. This preference affects PGS menus, controls and messages. Pokémon names, user data, external service content and technical runtime diagnostics keep their original values; Pokémon GO's own language remains independent.

See [the language guide and translation workflow](docs/PGS_LANGUAGES.md) for the complete language list, backup behavior, validation and translation maintenance.

<p align="center"><img src="website/public/images/main-menu.png" width="320" alt="PGS dark-theme main settings menu with feature sections and Discord footer"></p>

## Features and guides

The feature list and how-to guides live on the website, so there is one place to keep them current:

- **[PGS website](https://lucianotoscano.github.io/PGS/)**: overview, screenshots, and the cooldown chart.
- **[Feature guides](https://lucianotoscano.github.io/PGS/?guide=all)**: where each feature is in the app and how to use it.
- **[Changelog](CHANGELOG.md)** and [PGS releases](https://github.com/LucianoToscano/PGS/releases): PGS-only version history.

## Install PGS v0.0.4 (ARM64, non-root)

The current test candidate is PGS v0.0.4, built from the pinned original Pokemon GO 0.439.0 input and the migrated PGS source. Android versionCode is 2026111607. The existing PGS signing certificate and Android application ID are preserved.

- [Download PGS v0.0.4 (draft release)](https://github.com/LucianoToscano/PGS/releases/tag/untagged-a58384457d68bd85d972)
- [Successful complete build](https://github.com/LucianoToscano/PGS/actions/runs/46097341845)

The draft contains `PGS.v0.0.4.apk`, `PGS.json`, `build-info.json` and `SHA256SUMS.txt`. APK SHA-256: `9e48ba91d0c8e3ea9dcee2636d403bb2a335a8add74eae9dd5de1e14c917ddfc`. Draft downloads require repository access. Do not publish the original build-inputs draft.

The installed name remains Pokemon GO (`com.nianticlabs.pokemongo`). Installation, saved settings, gameplay and Google sign-in still require physical-device verification. Earlier releases remain available for reference.

## Good to know

These are experimental client modifications. Server outcomes are not guaranteed, the cooldown timer is a local estimate, and nothing here prevents account action by the game's publisher.

## Community

Join the [PGS Discord](https://discord.gg/SdwU4VnfW), also linked from the settings footer.

## Build and contribute

- [Build, signing, release CI, and installation](docs/BUILDING.md)
- [Architecture and compatibility](docs/ARCHITECTURE.md)
- [Root support (upstream reference; no PGS Root release)](docs/ROOTED.md)
- [Native migration verification and history](docs/NATIVE_MIGRATION.md)
- [Maintainability review and refactoring priorities](docs/MAINTAINABILITY.md)
- [Contributing and checks](CONTRIBUTING.md)
- [Third-party notices](THIRD_PARTY.md)

```powershell
python -B tools/check.py
```

Source CI runs device-free checks and compiles both the Android controls and the Root installer. Its downloadable artifact contains source and tools only, not a playable APK. The legacy **Android release (non-root and rooted)** workflow is intentionally blocked for PGS; only a dedicated PGS workflow may prepare a new signed game APK. Signing keys, original build inputs, and investigation logs are kept out of Git.

## Repository layout

```text
.github/workflows/    Source CI, release, and website workflows
docs/                 Build, architecture, and release notes
pgs/src/          Android UI and control bridge
pgs/native/       Compiled gameplay runtime and native tests
pgs/art/          Compiled Android runtime bridges
pgs/zygisk/       Legacy upstream Root loader (not released by PGS)
pgs/root-installer/  Legacy upstream Root installer (not released by PGS)
pgs/test/         Regression tests
pgs/vendor/       Pinned dependencies, provenance, and licenses
tools/                Checks, source packaging, release CI setup
website/              React site and feature guides, deployed to GitHub Pages
```

## License

The inherited source and PGS contributions are available under the [MIT License](LICENSE), retaining the original copyright and [attribution](NOTICE). Third-party components retain their own licenses. Pokémon GO and its assets are not covered by this license. PGS is an independent project and is not affiliated with the game publisher.
