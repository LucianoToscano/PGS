<p align="center"><img src="pgrazor/branding/pgrazor.svg" width="88" alt="PGRazor logo"></p>
<h1 align="center">PGS — Pokémon GO Spoofers</h1>
<p align="center">A compact Android interface for location controls and Pokémon GO automation.</p>

PGS, based on PGRazor, adds an in-game menu, an independent joystick, encounter controls, and optional automation to Pokémon GO. Settings persist across restarts, with light and dark themes.

## PGS community integration

PGS preserves the complete PGRazor source tree and its MIT/third-party notices. This fork starts from PGRazor **v0.3.8**, commit `1106592aa045759f55f594ff6968f783ff636fe9`, for Pokémon GO **0.439.0 / 2026111602**. Internal packages, saved-setting keys and the original interface identity remain compatible with that base.

The current candidate adds the joystick direction lock, a direct gift shortcut, configurable LivePokeMap refresh, populated wild-encounter IVs for VGP+, owned-IV refresh/layer fixes, real-GPS readiness, buddy timeout recovery and the Silver Pinap preference migration. Android packaging also works on Linux with the pinned toolchain.

- Hold the joystick centre for **1.5 seconds**, drag and release to lock direction; hold the padlock for **0.5 seconds** to stop. Leaving the map or losing the camera releases it.
- Open **Quick Menu → Send & Open Gifts** for the existing batch dialog; press Start there when ready.
- In **Shundo Sniper**, choose **LivePokeMap refresh**. The default is five minutes; server limits can require a longer wait. The feed's **Global** view refreshes manually.
- See [the PGS integration review](docs/PGS_COMMUNITY_REVIEW.md) for source attribution, what was already present, remaining proposals and validation limits.

PGS candidate artifacts are produced in [this repository's Actions](https://github.com/LucianoToscano/PGS/actions). Upstream PGRazor download links are not PGS updates. Compilation and automated fixtures do not establish Android installation or gameplay results; those observations are recorded separately.

The settings panel is grouped into Play, Automation and App cards, with an instant search field at the top. Search matches names, descriptions, categories and common synonyms (for example "fake gps" or "light mode"), and tapping a result opens the page, expands any collapsed section, and scrolls straight to that row.

## PGS interface languages

Open **Settings → Display & Performance → Language → PGS language**, choose a language, then fully close and reopen the game. The choices are **System, Deutsch, English, Español, Français, Português, Русский, Italiano, 繁體中文, Nederlands, ภาษาไทย and 한국어**. The selected language is shared by all accounts and included in explicit settings backups. The interface keeps its current language until the process restarts.

Translations are bundled offline. Search accepts both the selected language and the original English setting names. System follows the device language, using English if it is unsupported; Portuguese uses the Brazilian catalog and Chinese uses the Traditional Chinese catalog. This preference affects PGS menus, controls and messages. Pokémon names, user data, external service content and technical runtime diagnostics keep their original values; Pokémon GO's own language remains independent.

See [the language guide and translation workflow](docs/PGS_LANGUAGES.md) for the complete language list, backup behavior, validation and translation maintenance.

<p align="center"><img src="website/public/images/main-menu.png" width="320" alt="PGRazor dark-theme main settings menu with feature sections and Discord footer"></p>

## Features and guides

The feature list and how-to guides live on the website, so there is one place to keep them current:

- **[PGS website](https://lucianotoscano.github.io/PGS/)**: overview, screenshots, and the cooldown chart.
- **[Feature guides](https://lucianotoscano.github.io/PGS/?guide=all)**: where each feature is in the app and how to use it.
- **[Changelog](CHANGELOG.md)** and [PGS releases](https://github.com/LucianoToscano/PGS/releases): PGS-only version history.

## Instalação do PGS v0.0.1 (ARM64, sem root)

A primeira candidata completa da linha própria do PGS é **v0.0.1**, baseada em Pokémon GO **0.439.0**. O build usa o certificado definitivo PGS e Android `versionCode=2026111604`. A instalação, o login e a atualização física sobre uma instalação existente ainda precisam de confirmação no aparelho.

1. Acesse o [workflow de build do PGS v0.0.1](https://github.com/LucianoToscano/PGS/actions/workflows/pgs-v0.0.1-release.yml), escolha a execução concluída com sucesso na branch `main` e baixe o artefato **PGS-v0.0.1**. O GitHub pode exigir login.
2. Extraia o ZIP do artefato. O **APK completo** dentro dele se chama `PGS v0.0.1.apk`, acompanhado por `PGS.json` e `SHA256SUMS.txt`. Não instale o ZIP ou um APK de prévia.
3. Confira o SHA-256 do APK usando `SHA256SUMS.txt` e instale-o **sobre a versão PGS existente**, sem desinstalá-la para não perder dados. Registre a mensagem exata do Android se houver falha.
4. Ao abrir, confira o cabeçalho **PGS v0.0.1**, o convite do [Discord do PGS](https://discord.gg/SdwU4VnfW) e o menu do jogo. Um APK assinado e compilado com sucesso ainda não comprova funcionamento físico.

O **nome instalado continua Pokémon GO** e o pacote Android permanece `com.nianticlabs.pokemongo`. A assinatura é a [chave PGS definitiva](docs/PGS_UPDATE_POLICY.md); PGBR, PGSharp e PGRazor continuam separados. Uma instalação Play Store usa outro certificado e não pode ser substituída por atualização comum preservando dados.

O GitHub normaliza espaços para pontos ao criar um asset de Release: o arquivo do artefato Actions é `PGS v0.0.1.apk`, mas o asset do Release chama-se `PGS.v0.0.1.apk`. **São o mesmo APK assinado** após a cópia/validação por SHA-256. O release GitHub está preparado como **rascunho**, aguardando validação física antes de ser publicado.

A partir desta versão, o atualizador interno só consulta os releases do repositório PGS. O PGS antigo ainda consulta o PGRazor, portanto a passagem inicial para v0.0.1 é feita manualmente.

**Créditos:** PGS mantém os avisos e a base MIT do [PGRazor original](https://github.com/jpitty03/PGRazor); um APK do PGRazor original não deve ser usado como atualização do PGS.

## Good to know

These are experimental client modifications. Server outcomes are not guaranteed, the cooldown timer is a local estimate, and nothing here prevents account action by the game's publisher.

## Community

Join the [PGS Discord](https://discord.gg/SdwU4VnfW), also linked from the settings footer. PGS acknowledges the independent upstream PGRazor project and its contributors.

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

Source CI runs device-free checks and compiles both the Android controls and the Root installer. Its downloadable artifact contains source and tools only, not a playable APK. The legacy **Android release (non-root and rooted)** workflow is intentionally blocked for PGS; only a dedicated PGS workflow may prepare a new signed game APK. Signing keys, original build inputs, and investigation logs are kept out of Git.

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
