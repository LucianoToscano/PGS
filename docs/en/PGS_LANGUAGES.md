# PGS — In-app languages

[🇺🇸 English](PGS_LANGUAGES.md) · [🇧🇷 Português (Brasil)](../pt-BR/PGS_LANGUAGES.md)

## Changing the language

Open **Settings → Display & Performance → Language → PGS language**, select a language, then close and restart the game. PGS applies the saved selection on the next launch; switching languages does not automatically shut down the game.

In Portuguese, the path is **Configurações → Exibição e desempenho → Idioma → Idioma PGS**.

| Selector option | Language | Saved code |
|---|---|---|
| Sistema / System | Follow device language | `system` |
| Deutsch | German | `de` |
| English | English | `en` |
| Español | Spanish | `es` |
| Français | French | `fr` |
| Português | Brazilian Portuguese | `pt-BR` |
| Русский | Russian | `ru` |
| Italiano | Italian | `it` |
| 繁體中文 | Traditional Chinese | `zh-Hant` |
| Nederlands | Dutch | `nl` |
| ภาษาไทย | Thai | `th` |
| 한국어 | Korean | `ko` |

Language names are shown in their own language to make it easier to recover from a mistaken selection. The System label follows the active language.

## Preferences and compatibility

- The choice is global to the app. Changing game accounts or toggling shared settings does not change the interface language.
- Without a saved selection, PGS follows the system language. Unsupported device languages fall back to English. All Portuguese variants use the Brazilian catalog; supported Chinese variants use the available Traditional Chinese catalog.
- The choice is written atomically to `pgs-language-v1.properties`, independently of account profiles. Failed writes retain the prior selection and display an error.
- Explicit settings exports include `pgsLanguage`. Importing an older backup without the field preserves the existing language. Invalid values are rejected before the backup is applied.
- Imported language choices also require a restart. The translator does not change during a running session, including Activity recreation.
- PGS localization does **not** call `Locale.setDefault`, change the base game's resources, coordinates, protocol formats, or internal identifiers.

Menus, buttons, fixed options, accessibility descriptions, confirmations, and local interface messages use language catalogs. Pokémon names, accounts, favorites, route names, external service responses, technical errors, and diagnostic logs retain their original values. The setting does not change Pokémon GO's own language or translate Pokémon names in filters.

## Settings search

Settings search matches localized labels and descriptions **and** their English equivalents. Results open the same controls and keep the same identifiers. Search normalization ignores Latin accents while preserving relevant characters in other scripts.

## Maintaining translations

Editable catalogs are under `pgs/i18n/*.json`. `en.json` contains the canonical English keys, whose values equal their keys. Every other catalog must contain exactly the same set of keys.

After editing the JSON catalogs, run from the repository root:

```sh
python -B tools/i18n_catalog.py
python -B tools/check.py
```

The generator creates `I18nCatalog.java` and one class per language under `pgs/src/dev/pgs`. These files are committed so Android controls can compile offline without base-APK resources. CI rejects stale generated classes, missing or extra keys, duplicates, and incompatible format placeholders.

Use `I18n.t` for fixed texts and `I18n.format` for messages with data. Prefer indexed parameters (`%1$s`, `%2$d`) when translations may need another argument order. Preserve all placeholders, argument types, precision, and literal `%%`. Passed values remain opaque. `I18n.options` is only for fixed UI lists and must not be applied to names or user data.

Keep saved preference codes, JSON field names, state-machine phases, URLs, commands, bitmasks, and native identifiers canonical. Translate labels only where they are displayed. Settings-search fields retain canonical keys separately from displayed labels.

## Verification

Tests cover selection, fallback, persistence in a new process, account-independent preferences, legacy backup import, bilingual settings search, argument preservation, and invalid formats. Catalog tests compile the actual Java tables and check all language content after generation.

Android build, signing, and packaging verification supplement these tests. Installation, readability at each screen size, assistive technology, and actual gameplay require physical-device observation; unit tests are not a substitute.

## Website languages are separate

The GitHub Pages website supports English and Brazilian Portuguese separately from the **12 in-app language choices**. Changing the website language never changes the Android game's preference or language catalogs.
