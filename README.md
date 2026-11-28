<p align="center"><img src="pgs/branding/pgs.svg" width="88" alt="PGS emblem (upstream drawing retained)"></p>
<h1 align="center">PGS — Pokémon GO Spoofers</h1>
<p align="center">A compact Android interface for location controls and Pokémon GO automation.</p>

PGS, based on PGS, adds an in-game menu, an independent joystick, encounter controls, and optional automation to Pokémon GO. Settings persist across restarts, with light and dark themes.

## PGS community integration

PGS preserves the complete PGS source tree and its MIT/third-party notices. This fork starts from PGS **v0.3.8**, commit `1106592aa045759f55f594ff6968f783ff636fe9`, for Pokémon GO **0.439.0 / 2026111602**. Internal packages, saved-setting keys and the original interface identity remain compatible with that base.

The current candidate adds the joystick direction lock, a direct gift shortcut, configurable LivePokeMap refresh, populated wild-encounter IVs for VGP+, owned-IV refresh/layer fixes, real-GPS readiness, buddy timeout recovery and the Silver Pinap preference migration. Android packaging also works on Linux with the pinned toolchain.

- Hold the joystick centre for **1.5 seconds**, drag and release to lock direction; hold the padlock for **0.5 seconds** to stop. Leaving the map or losing the camera releases it.
- Open **Quick Menu → Send & Open Gifts** for the existing batch dialog; press Start there when ready.
- In **Shundo Sniper**, choose **LivePokeMap refresh**. The default is five minutes; server limits can require a longer wait. The feed's **Global** view refreshes manually.
- See [the PGS integration review](docs/PGS_COMMUNITY_REVIEW.md) for source attribution, what was already present, remaining proposals and validation limits.

PGS candidate artifacts are produced in [this repository's Actions](https://github.com/LucianoToscano/PGS/actions). Upstream PGS download links are not PGS updates. Compilation and automated fixtures do not establish Android installation or gameplay results; those observations are recorded separately.

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

## Instalação do PGS v0.0.2 (ARM64, sem root)

A nova candidata da linha PGS é **v0.0.2**, baseada no mesmo Pokémon GO **0.439.0**, com Android `versionCode=2026111605` e **a chave PGS definitiva**. Esta geração incorpora as alterações de identidade da PR #33, mantendo a logo interna do menu, o joystick, as preferências e as bibliotecas originais do jogo.

1. Abra o [workflow de build PGS v0.0.2](https://github.com/LucianoToscano/PGS/actions/workflows/pgs-v0.0.2-release.yml), selecione uma execução **bem-sucedida na branch main**, e baixe o artefato `PGS-v0.0.2`. O GitHub pode solicitar login.
2. Extraia o ZIP e use **`PGS v0.0.2.apk`** (jogo completo), acompanhado de `PGS.json` e `SHA256SUMS.txt`. Verifique o checksum indicado pela build antes de instalar.
3. Instale sobre a cópia PGS já existente **sem desinstalá-la**, preservando dados. Isso exige o mesmo certificado e `versionCode` maior; não tente atualizar PGBR, PGSharp ou o PGS separado.
4. Confirme instalação, abertura, login, cabeçalho **PGS v0.0.2**, Discord `https://discord.gg/SdwU4VnfW` e configurações salvas. **Ainda não existe evidência de teste físico**.

O nome instalado permanece **Pokémon GO**, com pacote `com.nianticlabs.pokemongo`. A Play Store usa outra assinatura e não pode ser atualizada em cima pelo PGS preservando dados. O GitHub mantém o APK com espaços no artefato Actions, mas normaliza o asset do Release para `PGS.v0.0.2.apk`; os dois nomes devem compartilhar o mesmo SHA-256.

A **v0.0.1** permanece como candidata anterior em seu próprio [workflow](https://github.com/LucianoToscano/PGS/actions/workflows/pgs-v0.0.1-release.yml), e seu rascunho não deve ser modificado. Os releases PGS só serão publicados como estáveis após testes no aparelho. Créditos da base [PGS original](https://github.com/jpitty03/PGS) e licenças são preservados.

## Good to know

These are experimental client modifications. Server outcomes are not guaranteed, the cooldown timer is a local estimate, and nothing here prevents account action by the game's publisher.

## Community

Join the [PGS Discord](https://discord.gg/SdwU4VnfW), also linked from the settings footer. PGS acknowledges the independent upstream PGS project and its contributors.

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

Original PGS source is available under the [MIT License](LICENSE). Third-party components retain their own licenses. Pokémon GO and its assets are not covered by this license. PGS is an independent project and is not affiliated with the game publisher.
