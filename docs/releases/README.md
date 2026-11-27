# PGS release notes — English primary

[🇺🇸 English](README.md) · [🇧🇷 Português (Brasil)](../pt-BR/README.md)

Release notes intended for GitHub and Discord are written in **English**. Official Brazilian Portuguese translations are maintained under `docs/pt-BR/releases/`. Both versions must be updated in the same PR.

For a new version, copy [TEMPLATE.md](TEMPLATE.md) to `docs/releases/vVERSION.md` and replace all placeholders. Keep signed APK names, Android `versionCode`, hashes and certificate identifiers identical in the translated copy.

- **New features:** explain changes briefly, only when present in the APK.
- **Improvements and fixes:** describe the outcome with concise bullets.
- **Compatibility:** state supported game version, Android package, and permanent signing certificate.
- **Validation:** clearly distinguish automated build verification from device installation and login. A draft does not imply a published stable release.
- **Links:** link only to verified PGS builds and source material. Never treat source archives or preview DEX files as complete APKs.
- **Legal notices:** keep copyright and third-party attribution intact. Do not alter the license.

The dedicated release workflow appends [footer.md](footer.md) to the canonical English notes and publishes only a verified candidate **as a draft**. The independent notes-sync workflow may update the **text of an existing draft**, but never modifies assets, certificates, tags, or published releases.

When real-device testing permits a release to be published, its announcement should stay in English and link to the Brazilian Portuguese notes. The in-app language selector is independent of GitHub documentation.
