# PGS Auth — independent foundation

Status: **authorization required; no live sign-in**.

This foundation is separate from the retired browser prototype and does not
change the currently installed application, signing key, manifest, game
authentication, account profiles, version ledger or build request. It contains
no borrowed client identities or provider secrets.

## Implemented

- `PgsAuthConfig`: fail-closed provider availability.
- `PgsAuthManager`: stable, non-sensitive diagnostic categories and preflight.
- `PgsAuthAttempt`: device-free lifecycle model for a future browser integration;
  opaque local handles, replacement, cancellation, timeout, single consumption.
  The model stores no provider credentials or authenticated sessions and is
  not wired to the game.
- JVM tests and static regression tests run with the existing source checks.

## Remaining authorization and implementation gates

1. Obtain documented authorization for the actual package/signing identity
   and provider configuration, including the service owner's acceptance of
   the client identity. Independent registration alone is insufficient.
2. Review an authorized SDK/system-browser integration, exact registered
   redirects, CSRF protection, PKCE where required, secure credential storage
   and session renewal. No app-to-game credential relay or provider-check
   circumvention is part of this foundation.
3. Test only an authorized test environment first; verify cancellation,
   consent, renewal, revocation, fresh login and safe account switching.
4. Review a separate change before enabling any production integration.
   Keep issue #72 open until the physical-device release gate passes.

## Português (Brasil)

A identidade do módulo é PGS Auth. Esta etapa entrega a base de configuração,
diagnóstico e ciclo de tentativas, sem abrir navegador, emitir tokens ou
autenticar contas do jogo. A autorização do provedor e do serviço do jogo
continua pendente. Não restaurar identificadores de terceiros nem publicar
uma versão que prometa corrigir o login antes da validação real.

Related: #38, #72.
