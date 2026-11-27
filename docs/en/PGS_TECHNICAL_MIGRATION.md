# PGS internal naming migration — Phase 1

**Current status (phase 15):** phase 12 already migrated Java/JNI, native library names and asset layout in source. The earlier sections below are historical records, not the current build layout. A complete signed APK and physical-device upgrade have not been verified.

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

The source compiler in `pgs/build.py` now reads `PGS_VERSION`, `PGS_BUILD_TOOLS`, and `PGS_ANDROID_PLATFORM` as its primary settings. The existing `PGRAZOR_*` spellings are retained as fallback aliases, so existing GitHub Actions workflows and local scripts keep their behavior without rewriting build configuration. When both are set, the nonempty PGS value takes precedence; empty values fall back.

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

## Phase 9 — bulk source identity migration

A single reviewable batch updates 34 native production source files and 12 native test/bridge fixtures to call or define the primary PGS hook engine symbols (`pgs_hook`, `pgs_unhook`, `pgs_instrument`). The legacy engine wrappers and the compatibility regression remain intact. Weak/dynamic lookup consumers (`interaction_host.cpp`, `camera_host.cpp`, `runtime_host.cpp`) and their fixtures are deliberately excluded. Only identifier spelling changes; no new hook, altered target, argument, order, data layout, or behavior is introduced.

Five workflows use the PGS-first non-secret build settings (`PGS_BUILD_TOOLS`, `PGS_ANDROID_PLATFORM`, `PGS_VERSION`). The SDK test readers accept the new settings first and the legacy aliases second, preserving defaults. Secret references and values, signing, the release ledger, the APK, Java/JNI namespace, installed library names, stored data, licenses and the project directory are unchanged. Two additional source guards cover the batch and workflow names. Source checks and host regressions are required before merge; they are not a signed Android build or physical installation test. A temporary backup branch preserves the pre-bulk baseline. Remaining work: [issue #38](https://github.com/LucianoToscano/PGS/issues/38).

## Phase 10 — repository project directory

The Git-tracked project root moves from the legacy folder to pgs/. Source paths, build entrypoints, generators, tests, documentation and CI are updated together. Installed Java/JNI names, assets and module paths, native exports/SONAMEs, preferences, signing identity, release and version ledger are not renamed by this checkout-only migration. Existing local build/input files are not moved or deleted by Git and remain ignored at their former path; move only your own reviewed local inputs to the new folder as needed. The historical v0.0.2 candidate build is manual-only to avoid regenerating the same signed version on routine maintenance. Source checks do not establish a device upgrade.

## Phase 11 — bulk native constant and type aliases

A single batch updates 98 native implementation/test files and five declaration headers: 438 source identifier uses migrate to 55 PGS names (33 numeric constants and 22 typedef names). Fifty-two aliases are introduced and three previously established type aliases are reused. The original constant literals, typedef definitions, struct tags, binary types, field layouts, and existing exported function names are retained. String literals, generated headers, preprocessor consumers, and externally configured names are deliberately excluded from automatic consumer substitutions. The [alias inventory](../PGS_NATIVE_ALIAS_INVENTORY.json) records each exact mapping. Linux C++17 static assertions compare all 55 constant values or type identities, alongside source checks and existing regressions.

The temporary migration job is not included in this commit. Existing package, signer, version ledger, APK, JNI namespace, installed library names, stored data, and licenses are unchanged. Host compilation and source checks do not prove the full signed APK or a physical-device upgrade. The backup branch remains available; the remaining migration is tracked in [issue #38](https://github.com/LucianoToscano/PGS/issues/38).

## Phase 12 — coordinated runtime identity

The new source layout moves Java classes to `dev.pgs` and updates generated DEX bridges, manifests, Java test fixtures, JNI registrations, and Root loader class names in the same batch. New builds use `libpgs-core.so`, `libpgs-art.so`, `pgs.dex`, and `assets/pgs/`. The existing factory ABI alias, installed Android game package, preview and Root installer application IDs, Root module ID and durable Off flag remain compatibility contracts. Asset and DEX input checks reject both old and new already-patched layouts; historical verifiers can read either asset root.

All new logical profile/file/preference names resolve through an explicit allowlist to their existing physical storage IDs. Existing account directories, AtomicFile recovery files, preference XML, backup schema and AndroidKeyStore aliases are deliberately not renamed, copied, deleted, or reset. This preserves compatibility for existing settings and account data; it is not a physical on-device data migration. The original v0.0.2 controls-only rebrand tool and historical source are retained; both historical workflows now refuse the new layout before compiling or signing, because the old complete APK contains incompatible native/DEX references. Any future release must rebuild the complete runtime together with the original permanent signing identity and a strictly higher versionCode, then pass real-device upgrade tests.

CI runs the consolidated source suite and adds a no-signing Android native build of the core and ART libraries for arm64-v8a and x86_64, including ELF SONAME checks. Only the final PR and main pushes trigger regular CI; the Android native job runs on PR/manual events. No game input, signing key or complete APK is required for this validation. This does not prove a physical install or account migration. Track remaining compatibility contracts in [issue #38](https://github.com/LucianoToscano/PGS/issues/38) and in-place testing in [issue #24](https://github.com/LucianoToscano/PGS/issues/24).

## Phase 13 — project attribution and remaining source paths

PGS contributions have their own copyright notice under MIT, alongside the unchanged original notice. The license index preserves third-party and artwork exclusions. The unused legacy forwarding header has moved to `pgs_native_api_compat.h`; external source clients using the old include path must update their include to `pgs_native_api.h` (or the new forwarding header). Both exported ABI factories, existing typedef aliases, struct tags and persisted storage identifiers remain intact. Hidden ART publication helper names and existing PGS account typedef consumers use the PGS spelling without changes to behavior or layout. Candidate preflight tests now explicitly exercise PGS-first version overrides and the legacy fallback.

## Phase 14 — remaining active names and full inventory

Use PGS names for Java thread labels, diagnostic tags, disposable cache directories, UI descriptions, and existing native typedef/macro consumers. Temporary-directory cleanup accepts both previous and current names. Non-secret runtime build options now accept PGS names while retaining the previous opt-in aliases. No persistent storage identifiers, Android package IDs, signing configuration, or binary ABI exports change in this phase. The [tracked-text inventory](../PGS_REMAINING_REFERENCES.json) records the remaining original-name references by file and category; it is a snapshot for review, not a declaration that every remaining reference is necessary. Binary content and temporary migration files are excluded. Legal attribution and historical release records stay intact. Full source and native ABI validation are required before integration.


## Phase 15 — native source aliases and reproducible audit

The new source aliases for equivalent enum values and function pointer types preserve the original enum type, numeric values, pointer signatures, struct tags, layout, ABI exports and dynamic lookup strings. The existing C++17 regression now checks enum type identity and that the legacy enumerators are not macros. File-local helper names and equivalent active references use the PGS spelling. No native feature behavior or protection policy changes.

Run `python -B tools/pgs_reference_inventory.py --summary` from a Git checkout for a fresh read-only scan. Omit `--summary` for per-file counts. The general source CI runs the inventory test; the checked-in snapshot is an exact delta from the preceding inventory, not yet an independent scan. The new tool's UTF-8/NUL rule is explicit; differences in scope must be reconciled before comparing snapshots.

### Classification for remaining work

- Replaceable now: verified equivalent source-only constants, types, private helpers, and non-contract display or diagnostic labels.
- Coordinated migration: hidden native getters and their weak/dynamic lookups, JS bridge names, DEX rewriter method prefixes, and runtime object names. Review every producer, consumer and fixture before changing these.
- Compatibility: physical account and preference identifiers, AndroidKeyStore and notification channel IDs, Root and preview application/module IDs, old-input rejection markers, existing signing configuration and environment fallbacks. Preserve until an explicit compatible migration is established.
- Attribution/license and historical records: retain original notices and prior release/build records.
- Compatibility tests: retain assertions of old identifiers where they specifically prove fallback, ABI identity, input rejection or data continuity. Ordinary consumers may use verified equivalent PGS names.

Remaining occurrence counts are not a determination that all remaining references are necessary. A complete signed release, authorized input, and physical-device testing are separate gates. No APK or ledger update is part of this batch.

## Phase 16 — canonical factory consumers and inventory reconciliation

The active JS loader resolves `pgs_native_api` first and uses the existing legacy export only if the primary symbol is absent. It retains the exact previous ABI checks and never falls back on an ABI validation error. Ordinary native test fixtures now resolve the PGS factory; an explicit integration fixture verifies identical v1/v2 pointers and unsupported-version rejection through both exports. The JS fixture checks primary lookup, compatibility fallback, missing symbols and existing ABI rejection. Neither export nor feature behavior changes.

Phase 15 independent CI reported 2,468 references in 539 files, from 1,031 UTF-8 text files among 2,106 tracked paths (snapshot excluded). The checked-in delta snapshot reported 2,477 references. The difference is nine references and one matching file in the native category; its precise cause is not established. Phase 16 preserves exact deltas against the checked-in snapshot and adds `--compare-snapshot` to report the differing paths and counts from a fresh scan, including during CI. Reconcile the scope before declaring an exact new independent count. License, data keys, old input rejection, release history and signing contracts are untouched. No APK issuance or physical-device verification is implied.

## Phase 17 — indexed source audit and remaining factory consumers

Phase 16 CI found exactly one discrepancy in its checkout-based inventory: nine references in `pgs/native/account_host.cpp`. The initial connector text view suggested valid UTF-8, but the raw-blob request rejected the source and the indexed and working-tree CI scans both excluded it. The inventory follows the reproducible CI scope; the original source bytes are not rewritten. The source file is preserved, and the audit now reads indexed blob bytes with `git cat-file --batch`, independent of checkout filters or test-generated changes. A separate worktree mode reports any differences; indexed per-file counts must match the checked-in snapshot. A temporary Git repository test proves that staged counts do not follow untracked or modified checkout files.

The remaining ordinary C++ test fixtures with direct legacy-factory lookups have been migrated to the canonical factory. Explicit ABI parity coverage and internal fixture linkage symbols remain intact. No native feature implementations, game behavior, persisted keys, licenses, signing, versions or APKs are modified. A small documentation and build identification cleanup also updates the current source directory and HTTP user agent.

## Consolidated Phase 17 — bulk identity migration

One coordinated pull request migrates 63 private native feature getter names and their declarations, definitions, registry references, internal string lookups, and test consumers. The reviewed native, test, Java, and build-tool scope comprises 391 paths. All 14 affected runtime/diagnostic JavaScript files and 15 matching JS fixtures adopt PGS naming. The existing public compatibility factory, the native getter dependencies of the excluded account source, and the translated snapshot error-code contract remain intact. The IV fixture prefers the canonical factory and falls back only when its legacy-only mock has no primary export. Signing, persistent storage keys, licenses, original attribution, feature logic, and release data are outside this rename. All edits are staged together before one complete source-check run; no compatibility or physical-device result is claimed before validation.

## Phase 18 — consolidated source identity cleanup

Use the canonical PGS spellings in direct native calls. Eight private source-level getter wrappers forward the version unchanged to the existing hidden linkage; no new dynamic export, table layout, or feature behavior is introduced. The original symbols remain available to older objects, weak-link fixtures and the source excluded from the UTF-8 inventory. Additional existing type/constant aliases, file-local macro spellings, current comments, temporary-directory names and installer display strings use PGS. The root module's physical paths, command output, Android identities, persisted storage, notification channels, signing, history and license attribution are intentionally unchanged. Synthetic native getter tests and installer display assertions verify the new source spelling. The preceding phase-17 CI independently reconciled all 1,728 references without indexed/checkout differences. Phase 18 uses exact indexed deltas until the full source CI confirms the new counts.

## Phase 19 — bulk primary identity migration

Canonical PGS types are now the original definitions, and legacy typedef aliases refer back to those definitions. Seven private getters are implemented and consumed under their PGS names, with compatibility wrappers for existing source consumers. The account-host source has been kept byte-for-byte because the connector's reconstructed text did not match its original Git blob hash; its existing calls continue through the compatibility interfaces. The public factory retains both exported names, and camera/spawn consumers prefer the canonical factory. Private gym-repeat getter spelling, selected diagnostic log tags, internal UI object names and all identified active source consumers and test fixtures were updated together. No game behavior, table layout, persisted data, signing, original license or APK has been altered. Legacy tag-qualified C++ source names are not guaranteed; typedef compatibility and the public binary ABI are retained. The full CI suite must confirm the candidate before integration.

### Consolidated current-name cleanup

New mode assets use `pgsVersion`. The candidate verifier requires that field and rejects contradictory legacy metadata; the historical bundle verifier continues to accept correctly versioned older assets. Native prerequisite instructions and generated environment receipts use the PGS variables, with existing input fallbacks untouched. Current header descriptions, internal diagnostic names and their synthetic tests have been updated together. Repository settings describe the current paths, not the retired layout. No change to signing, existing APKs, protected storage identifiers, public ABI exports, or original legal notices. The remaining text inventory includes historical records, upstream provenance, deliberately retained contracts, and tests of those contracts. Do not use a literal zero-match search as proof of migration or erase evidence merely to reduce a counter. Any unresolved occurrence must be reviewed before claiming that all substitutable references are gone.

## Final identity review after phase 19

PR #61 is integrated, with successful full source CI on its head and successful post-merge source CI. The new source-level cleanup uses canonical PGS names in direct camera calls and account-host test calls, and updates root loader diagnostic branding without changing its on-disk markers or control flow. The historical native migration notes are labeled as history, not current build instructions.

The indexed reference snapshot now groups every remaining matching file by retention purpose or unresolved migration dependency. This is a file-level triage, not proof that every individual occurrence is indispensable. Preserve original attribution, recorded history, explicit legacy guards, installed identities, encrypted storage, signer identity and ABI compatibility. Weak-link interfaces still need coordinated review before retiring the old names. The account-host implementation remains outside the strict UTF-8 inventory; do not rewrite it through a reconstructed text response. The external feed must have a verified, authorized replacement before changing its endpoint; the independent feed work is tracked separately in PR #62. No APK has been generated or installed by this review.

## Abbreviated native identity cleanup

The earlier full-name inventory did not count the separate `PGR_`, `pgr_` or `PgrCamelCase` spellings. The extended indexed-text scanner now reports these forms separately with exact per-file counts; the previous full-name series is retained for comparison. This source-only batch canonicalizes 258 distinct names and 1,600 uses across the account, spin, spawn, map tap, map POI, VGP auxiliary and battle headers and their identified consumers. Constants, enum values, structure members, layout assertions, API versions and public exports are unchanged. Internal private C++ types are rebuilt together; retirement of older source spellings is not a promise of compatibility with separately compiled private objects. The original account-host blob cannot be verified through reconstructed connector text and is retained byte-for-byte. Its sixteen identified legacy constant names remain as source aliases in `account_source_compat.h`. This is not an exhaustive abbreviation migration: the full CI inventory will establish the remaining count and verify the proposed names. The independent feed branch, signing identity, installed application data, release artifacts and original notices are unchanged.

## Private source alias retirement and canonical new artifacts

The earlier compatibility phases are historical. PR #65 now removes 125 equivalent C/C++ type/constant aliases and 12 private getter/hook wrappers, updates their consumers and checks the original LP64 size, alignment and value facts. The public binary factory and explicit legacy-input rejection checks remain. Newly generated DEX bridge bodies use the PGS prefix. New settings exports use schema version 2 with PGS scope names; version-1 backups remain importable. The physical preferences and encrypted vault identifiers are unchanged. An older build that only understands version 1 cannot read version-2 exports. Verified Dobby caches migrate their disposable receipt only after validating the archive and source files. Root toggle receipts use PGS naming, while the actual installed module paths and Off marker remain unchanged. Full CI and signed APK/device verification are still separate gates.

## Final source identity and candidate boundary

New Root runtime cache payloads use the disposable PGS directory. Earlier fixed cache directories are not deleted or renamed; installed module identifiers and the user's Off marker remain unchanged. The public binary compatibility entry point, existing account-profile storage and encryption identifiers, notification channel IDs, historical input recognition, and signing secret fallbacks are retained deliberately. Changing these contracts requires independent migration and real-device tests. Source-name retirement is distinct from their retirement.

For the next full build, use the existing manual, authorized v0.0.3 validation workflow on main after CI passes. It verifies the complete signed candidate and uploads receipts only; it does not distribute game bytes or claim device acceptance. The repository is public. To test a complete APK on a physical device, an authorized maintainer must build and retain the signed candidate in a controlled environment. Do not advance the published version ledger or claim installation/login success without the corresponding evidence. All existing drafts, keys and backup branches remain preserved.
