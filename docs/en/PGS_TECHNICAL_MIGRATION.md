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
