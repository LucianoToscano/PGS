# PGS release notes / Notas de releases

English is the primary release language. Maintain a Brazilian Portuguese counterpart for every new version.

1. Copy [English template](TEMPLATE.md) to `docs/releases/vX.Y.Z.md`.
2. Copy [Portuguese template](../pt-BR/releases/TEMPLATE.md) to `docs/pt-BR/releases/vX.Y.Z.md`.
3. Replace all placeholders with the verified build receipt and actual validation results. Both files must start with the same version heading.
4. Run `python -B tools/pgs_release_notes.py vX.Y.Z` to render both languages and the common footer.
5. Use the manual **PGS — Sync bilingual release notes** workflow on the default branch. It edits an existing draft body only; no APK upload, signing, publishing, or Discord repost.
6. Approve publication separately. Only advertise actual assets; do not promise a Root release when none exists.

Português: copie os dois modelos, preencha com as evidências da compilação, gere as notas bilíngues e execute o workflow de sincronização. O rascunho continua privado até autorização de publicação.
