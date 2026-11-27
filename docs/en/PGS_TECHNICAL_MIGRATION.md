# PGS internal naming migration — Phase 1

Status: code migration started in `refactor/pgs-native-build-names-phase1`. No new signed APK is released by this phase.

[🇺🇸 English](PGS_TECHNICAL_MIGRATION.md) · [🇧🇷 Português (Brasil)](../pt-BR/PGS_TECHNICAL_MIGRATION.md)

## Completed source-level changes in this phase

| Before | PGS name | Compatibility |
| --- | --- | --- |
| `native/pgrazor_native.cpp` | `native/pgs_native.cpp` | exported C ABI unchanged |
| `native/pgrazor.map` | `native/pgs.map` | legacy `pgrazor_native_api` export retained |
| `native/pgrazor_internal.h` | `native/pgs_internal.h` | internal selfcheck renamed |
| `native/pgrazor_native_api.h` | `native/pgs_native_api.h` | old include path forwards to the PGS header |
| `art/pgrazor-art.map` | `art/pgs-art.map` | JNI_OnLoad export unchanged |
| CMake `pgrazor_core` / `pgrazor_art` | `pgs_core` / `pgs_art` | linked SO names unchanged |
| `PGRAZOR_NATIVE_PILOT` / `_DOWNLOAD` | `PGS_NATIVE_PILOT` / `_DOWNLOAD` | old variables still work |
| `PGRAZOR_ART_NDK` / `PGRAZOR_NATIVE_DEPS` | `PGS_ART_NDK` / `PGS_NATIVE_DEPS` | old variables still work |
| `nonroot.cmd` as Windows entry point | `pgs.cmd` | original .cmd forwards to new script |

## Do not break Android/ABI

The output binaries `libpgrazor-core.so`, `libpgrazor-art.so`, exported function `pgrazor_native_api`, existing DEX Java `dev.pgrazor` classes and `assets/pgrazor` **must stay unchanged for now**. Android package **`com.nianticlabs.pokemongo`**, display name **Pokémon GO**, permanent PGS signing certificate, update ledger and user data are untouched. Changing the binary names before updating every JNI loader, bootstrap component, test, and release verifier would break startup.

This phase is covered by new offline identity tests and existing CMake/native checks. It does not constitute physical-device testing or successful APK installation.

## Next phases

1. Migrate internal Java class packages with compatibility adapters and rebuild dex descriptors/JNI registrations.
2. Migrate native library/asset names with dual-read loaders, checksum verification and rollback.
3. Migrate stored preferences and backup keys without data loss.
4. Resolve the separate OAuth client/redirect integration with authorized credentials, not values borrowed from another application.
5. Rebuild a **complete** signed PGS APK and test in-place upgrade on a physical device before publishing.

Track the remainder in [issue #38](https://github.com/LucianoToscano/PGS/issues/38). Git history and MIT/third-party provenance are retained.

## Phase 2 — native include consolidation

The active first-party C++ modules and native test fixtures now include `pgs_native_api.h` instead of `pgrazor_native_api.h`. The compatibility forwarding header remains so older external includes still compile; public factory name, table layout and SONAME remain unchanged. An automated test scans native sources to reject reintroduction of old include paths.

This phase changes header references only, not runtime logic or the Android app identity. A complete, newly signed APK and an in-place update test are **not** implied by successful host regression tests.

## Phase 3 — primary PGS factory with preserved native ABI

- The new exported C factory `pgs_native_api(uint32_t)` is the primary name. The unchanged `pgrazor_native_api(uint32_t)` symbol forwards to it. Both names return **identical immutable v1/v2 tables** for supported versions, and null for unsupported versions.
- `pgs.map`, the ELF dynamic-export guard and the isolated native harness enforce exactly **three** exports: `JNI_OnLoad`, `pgs_native_api` and `pgrazor_native_api`. Other symbols remain hidden.
- Public header constants, result codes and function typedefs now support `PGS_*` / `pgs_*` spellings as primary source names, with the old spellings preserved as compatibility aliases. The size and field ordering of the v1/v2 ABI tables are unchanged.
- Android still loads `libpgrazor-core.so` and `libpgrazor-art.so`, and existing Java/JNI code may still resolve the legacy factory. No rename is applied to DEX package `dev.pgrazor`, data/backup paths, Android package `com.nianticlabs.pokemongo`, the established PGS signing certificate or the version code.
- This phase is validated by source checks and native symbol tests. It is **not** a complete signed APK build or a confirmed real-device upgrade. Remaining migration work stays in [issue #38](https://github.com/LucianoToscano/PGS/issues/38).

## Phase 4 — internal C++ hook engine naming

- The primary internal implementations are now `pgs_hook`, `pgs_unhook`, `pgs_instrument` and `pgs_hook_diag`. Previously compiled native call sites can still resolve `pgrazor_*` forwarding functions; all share the **same Dobby registry and mutex**.
- `PgsHookDiag` and `PgsPaddingRanges` are type aliases retaining the original ABI/layout and padding math. The active core uses the PGS names, and the native near-island regression exercises both names.
- Android hook failure messages use `PGS` as their log tag. No additional public ELF exports, changed SONAME, package/signing change, new gameplay hook or installed APK results from this phase.
- Later migrations will address Java/JNI, native library filenames, asset paths and persisted settings after real-device compatibility tests; see [issue #38](https://github.com/LucianoToscano/PGS/issues/38).

## Phase 5 — PGS-first non-secret Java build options

The source compiler in `pgrazor/build.py` now reads `PGS_VERSION`, `PGS_BUILD_TOOLS`, and `PGS_ANDROID_PLATFORM` as its primary settings. The existing `PGRAZOR_*` spellings are retained as fallback aliases, so existing GitHub Actions workflows and local scripts keep their behavior without rewriting build configuration. When both are set, the nonempty PGS value takes precedence; empty values fall back.

The `PGRAZOR_KEYSTORE`, alias and password variables, key file, preview paths, output DEX format, Android package, permanent certificate, and release-version ledger are **unchanged** in this phase. No new key is generated by this change. An isolated test verifies default/fallback/precedence and version validation without invoking a signer or Android SDK. A green source check is not a full signed game APK or physical installation test.

## Phase 6 — direct hook consumers (buddy feeding and inventory items)

The production `buddy_feeding.cpp` and `items.cpp` modules now call `pgs_hook` directly (two and five call sites, respectively). Their isolated Linux host fixtures define the matching primary symbol, so the existing compile-and-run regressions exercise the migrated consumers without the legacy forwarding name. The source identity test also guards these call sites against accidental reintroduction of `pgrazor_hook`.

The change is naming-only: hook arguments, installation order, original chaining, state, Dobby engine, C ABI, SONAME, JNI, package, signing, preferences and version ledger are unchanged. Legacy forwarding functions remain in the engine for other consumers; weak/dynamic lookup in `interaction_host.cpp` and `camera_host.cpp` is intentionally deferred. Integration requires successful source checks and Linux native regression jobs. Host fixtures do not prove real-device hook execution or APK installation; no complete APK is produced by this phase. See [issue #38](https://github.com/LucianoToscano/PGS/issues/38).

## Phase 7 — direct hook consumers (IV display and inventory host)

The existing direct hook calls in `iv_display.cpp` (two sites) and `inventory_host.cpp` (one site) use `pgs_hook`. Their linked fixtures (`iv_owned_refresh_test.cpp`, `inventory_berries_policy_test.cpp` and the generated registry shim in `test_iv_owned_refresh_native.py`) now provide the matching primary name. The existing Linux compile-and-run tests remain in place, with an additional source identity check preventing these consumers and fixtures from reverting to the legacy spelling.

Only names change. Hook targets, arguments, order, state, Dobby registry, existing ABI, JNI, SONAME, Android identity, signing and stored data are unchanged. The inventory policy fixture does not install social hooks, and neither Linux suite proves real Android instruction patching. Legacy engine forwarding functions and weak/dynamic consumers remain intact. Integration requires successful source checks and Linux regressions. No new APK is produced or released. Track remaining work in [issue #38](https://github.com/LucianoToscano/PGS/issues/38).

## Phase 8 — public source/tools archive name

The source-only package generated by `python -B tools/source_bundle.py` is now `dist/PGS-source-tools.zip`, and the Source checks workflow uploads it as `PGS-source-tools`. Archive selection, file contents, safety checks, working-tree allowlist, CI permissions and retention remain unchanged. Two regression tests verify the actual archive name and contents in a temporary Git checkout and the matching workflow upload settings.

The new filename applies to future packaging runs; historical artifacts and previously downloaded local archives are not renamed or removed. External scripts using the former filename must update their references. This archive contains source and tools, not an installable APK. No release, signing configuration, Android identity, persisted data or runtime ABI changes in this phase. Track remaining migration work in [issue #38](https://github.com/LucianoToscano/PGS/issues/38).
