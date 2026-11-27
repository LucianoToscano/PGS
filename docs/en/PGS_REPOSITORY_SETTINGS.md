# PGS repository settings (English / Português do Brasil)

[🇺🇸 English](PGS_REPOSITORY_SETTINGS.md) · [🇧🇷 Português (Brasil)](../pt-BR/PGS_REPOSITORY_SETTINGS.md)

## About description — English

The GitHub repository **About** description is an administrative setting, not part of README.md. Set it to:

> PGS — Pokémon GO Spoofers. Independent Android project with location controls, joystick, maps, and companion tools for Pokémon GO.

Open https://github.com/LucianoToscano/PGS, choose the **About** gear/edit control, paste the sentence and save. On a mobile browser, **Desktop site** may reveal the editing control. The GitHub code connection cannot edit this administrative field.

## Where is the Website workflow?

**Workflow name:** Website. **File:** `.github/workflows/pages.yml`.

- [Open the Website workflow](https://github.com/LucianoToscano/PGS/actions/workflows/pages.yml)
- [Last verified successful run #45990719478](https://github.com/LucianoToscano/PGS/actions/runs/45990719478)
- [GitHub Pages settings](https://github.com/LucianoToscano/PGS/settings/pages)

The November 27, 2026 run passed both **build** and **deploy**. Earlier failed runs remain visible in the historical Actions list; an old red X is not the status of the current `main`. From Actions, look for **Website** on the left (the GitHub mobile app may hide this list); use the direct workflow link when needed. A manual run is available through **Run workflow** on the web interface.

The site has a selector **EN / PT-BR** independent of the Android application's language settings.

## Why does code search still show the previous project's name?

The `pgrazor/` source tree, `dev.pgrazor` Java classes, `assets/pgrazor` runtime paths, native ABI names, and certain saved backup keys are **technical compatibility contracts**. Old Git history and backup branches are retained, not silently rewritten. Renaming these before an Android/JNI migration could prevent the signed PGS APK from starting or reading data.

Current PGS public display names and downloads must use PGS. The exact license attribution is retained. The migration of internal identifiers is tracked in [issue #38](https://github.com/LucianoToscano/PGS/issues/38) and requires automated tests, an unchanged Android package/certificate, a full signed APK, and real-device update testing. Do not delete historic backup branches or test fixtures simply to reduce search results.

The installed app remains **Pokémon GO**, package `com.nianticlabs.pokemongo`, using the established PGS signing certificate.
