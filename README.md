<p align="center"><img src="pgrazor/branding/pgrazor.svg" width="88" alt="PGRazor logo"></p>
<h1 align="center">PGS — Pokémon GO Spoofers</h1>
<p align="center">A compact Android interface for location controls and Pokémon GO automation.</p>

PGRazor adds an in-game menu, an independent joystick, encounter controls, and optional automation to Pokémon GO. Settings persist across restarts, with light and dark themes.

## PGS community integration

PGS preserves the complete PGRazor source tree and its MIT/third-party notices. This fork starts from PGRazor **v0.3.8**, commit `1106592aa045759f55f594ff6968f783ff636fe9`, for Pokémon GO **0.439.0 / 2026111602**. Internal packages, saved-setting keys and the original interface identity remain compatible with that base.

The current candidate adds the joystick direction lock, a direct gift shortcut, configurable LivePokeMap refresh, populated wild-encounter IVs for VGP+, owned-IV refresh/layer fixes, real-GPS readiness, buddy timeout recovery and the Silver Pinap preference migration. Android packaging also works on Linux with the pinned toolchain.

- Hold the joystick centre for **1.5 seconds**, drag and release to lock direction; hold the padlock for **0.5 seconds** to stop. Leaving the map or losing the camera releases it.
- Open **Quick Menu → Send & Open Gifts** for the existing batch dialog; press Start there when ready.
- In **Shundo Sniper**, choose **LivePokeMap refresh**. The default is five minutes; server limits can require a longer wait. The feed's **Global** view refreshes manually.
- See [the PGS integration review](docs/PGS_COMMUNITY_REVIEW.md) for source attribution, what was already present, remaining proposals and validation limits.

PGS candidate artifacts are produced in [this repository's Actions](https://github.com/LucianoToscano/PGS/actions). The upstream release links below describe the original PGRazor distribution. Compilation and automated fixtures do not establish Android installation or gameplay results; those observations are recorded separately.

The settings panel is grouped into Play, Automation and App cards, with an instant search field at the top. Search matches names, descriptions, categories and common synonyms (for example "fake gps" or "light mode"), and tapping a result opens the page, expands any collapsed section, and scrolls straight to that row.

<p align="center"><img src="website/public/images/main-menu.png" width="320" alt="PGRazor dark-theme main settings menu with feature sections and Discord footer"></p>

## Features and guides

The feature list and how-to guides live on the website, so there is one place to keep them current:

- **[PGRazor website](https://jpitty03.github.io/PGRazor/)**: overview, screenshots, and the cooldown chart.
- **[Feature guides](https://jpitty03.github.io/PGRazor/?guide=all)**: where each feature is in the app and how to use it.
- **[Changelog](CHANGELOG.md)** and [release notes](https://github.com/jpitty03/PGRazor/releases): what each version added.

## Install

There are two builds. Each release lists the Pokémon GO version it supports; native features are built for that exact version.

**PGRazor (no root).** One APK for ARM64 Android phones and the MuMu emulator.

1. Open [Releases](https://github.com/jpitty03/PGRazor/releases/latest) and download **PGRazor.apk**, not a source archive.
2. Open the APK on your device and allow installation from your file manager.
3. Launch **Pokémon GO** and tap the small **R** icon for the quick menu. Choose **Settings** for the full controls.

A Play Store install is signed with a different certificate, so PGRazor cannot update it in place; it replaces that copy.

**PGRazor Root (experimental).** For rooted devices using the official game. It installs a Zygisk module through Magisk 27+, KernelSU, or APatch and leaves the game's APK untouched. Download **PGRazor-Root.apk** from the same release and follow [the Root guide](docs/ROOTED.md).

Each release includes a changelog, SHA-256 checksums, and build information. See [installation and builds](docs/BUILDING.md) for details.

## Good to know

These are experimental client modifications. Server outcomes are not guaranteed, the cooldown timer is a local estimate, and nothing here prevents account action by the game's publisher.

## Community

Join the [PGRazor Discord](https://discord.gg/9QqfkDSQX3), also linked from the settings footer. If you enjoy PGRazor, you can support development on [Ko-fi](https://ko-fi.com/pgrazor). Donations are optional.

## Build and contribute

- [Build, signing, release CI, and installation](docs/BUILDING.md)
- [Architecture and compatibility](docs/ARCHITECTURE.md)
- [PGRazor Root](docs/ROOTED.md)
- [Native migration verification and history](docs/NATIVE_MIGRATION.md)
- [Maintainability review and refactoring priorities](docs/MAINTAINABILITY.md)
- [Contributing and checks](CONTRIBUTING.md)
- [Third-party notices](THIRD_PARTY.md)

```powershell
python -B tools/check.py
```

Source CI runs device-free checks and compiles both the Android controls and the Root installer. Its downloadable artifact contains source and tools only, not a playable APK. Playable releases come from the manually triggered **Android release (non-root and rooted)** workflow. Signing keys, original build inputs, and investigation logs are kept out of Git.

## Repository layout

```text
.github/workflows/    Source CI, release, and website workflows
docs/                 Build, architecture, and release notes
pgrazor/src/          Android UI and control bridge
pgrazor/native/       Compiled gameplay runtime and native tests
pgrazor/art/          Compiled Android runtime bridges
pgrazor/zygisk/       PGRazor Root loader
pgrazor/root-installer/  PGRazor Root installer app
pgrazor/test/         Regression tests
pgrazor/vendor/       Pinned dependencies, provenance, and licenses
tools/                Checks, source packaging, release CI setup
website/              React site and feature guides, deployed to GitHub Pages
```

## License

Original PGRazor source is available under the [MIT License](LICENSE). Third-party components retain their own licenses. Pokémon GO and its assets are not covered by this license. PGRazor is an independent project and is not affiliated with the game publisher.
