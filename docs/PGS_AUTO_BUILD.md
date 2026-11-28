# PGS AUTO BUILD — permanent candidate workflow

## English

The permanent workflow starts only when a validated, explicitly authorized build request changes on main, or when an authorized manual retry is made on main. The initial build-request.json is disabled. Do not enable it until an actual candidate is requested.

A request must name the next patch release, the previous verified APK digest and Android versionCode, the pinned game version/code and input SHA-256, and explicitly authorize input use and optional draft retention. The workflow checks the previous receipt and unused release/tag before building with the existing signer. It preserves the current browser-login build option and performs full source and candidate checks. It can retain the four verified non-root assets plus the matching Root installer, module ZIP and Root build receipt only in an unpublished draft. The Root candidate is independently checked for matching game target, package/version, signer, module contents and checksums. A Root failure is reported explicitly and does not invalidate or publish the separately verified non-root candidate; no automatic publication, signing key upload, game-input upload or replacement of an existing release.

Example schema (substitute verified ledger/profile/receipt values, never guess):
```json
{
  "schema": 1,
  "enabled": true,
  "version": "vX.Y.Z",
  "previous_version_code": 0,
  "previous_apk_sha256": "REPLACE_WITH_VERIFIED_DIGEST",
  "game_version": "REPLACE_WITH_PROFILE",
  "game_version_code": 0,
  "input_sha256": "REPLACE_WITH_PINNED_DIGEST",
  "authorized_input": true,
  "retain_authorized_candidate": true
}
```

For a failed build with no existing candidate or tag, an explicitly authorized retry may increment the optional integer retry_attempt (1–100) in the committed request. Maven artifacts retain their exact SHA-256 pins, use bounded backoff honoring Retry-After, and may use the documented Google Cloud Maven Central mirror. No integrity check is relaxed.

Only approve a release and advance the version ledger after device testing and explicit authorization. Existing per-version workflows remain historical; use the permanent workflow for new requests. After handling a request, reset build-request.json to its disabled schema before allocating another version.

## Português (Brasil)

O workflow permanente gera uma candidata somente com pedido versionado e autorização explícita na main, ou repetição manual autorizada. O arquivo inicial está desativado. Verifica a versão seguinte, recibo anterior, hash de entrada, certificado, código Android crescente e testes. Mantém a configuração de login do build validado anterior. Se autorizado, guarda os quatro arquivos verificados não-root e, quando a validação Root também passa, o instalador Root, o módulo ZIP e o recibo Root, em rascunho. Se Root falhar, o workflow sinaliza a falha e pode conservar apenas a candidata não-root já verificada; não publica, não substitui releases e não exporta chaves nem o jogo original. A publicação e a atualização do registro de versões exigem aprovação separada e teste no aparelho. Após uma falha e sem candidata/tag existente, uma repetição explícita pode incrementar retry_attempt (inteiro de 1 a 100) no pedido. Dependências Maven conservam o SHA-256 fixado, respeitam Retry-After, têm tentativas limitadas e podem usar o espelho oficial hospedado pelo Google Cloud.

## Explicit publication for the v0.0.6 updater test

The owner authorized public distribution of the exact verified v0.0.6 candidate before physical-device testing so the updater can be tested from v0.0.5. This is a one-version exception, not a general relaxation of the device-test gate. The unchanged receipts record device_tested=false and publish_ready=false at build time; public release notes record the later owner-confirmed in-app update and owner acceptance of the other first-audit items, without separate detailed logs for five functional/Root tests. The signed Android code is reserved in the version ledger and the handled request is disabled. The previous release remains available.

O responsável autorizou excepcionalmente a publicação da candidata verificada v0.0.6 para testar a atualização interna a partir da v0.0.5. Os recibos permanecem intactos, as notas públicas registram a atualização interna comprovada por capturas e o aceite do responsável dos demais itens da auditoria, sem registros detalhados separados para cinco testes funcionais/Root e esta autorização não se estende a versões futuras. O código Android assinado fica reservado no registro de versões e o pedido de build concluído é desativado.
