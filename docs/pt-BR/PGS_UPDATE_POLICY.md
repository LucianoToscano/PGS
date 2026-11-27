[🇺🇸 English](../en/PGS_UPDATE_POLICY.md) · 🇧🇷 Português (Brasil)

# Continuidade das atualizações do PGS

O PGS **não** muda de identificador. O arquivo se chama `PGS.apk`, mas o pacote e o nome instalado continuam sendo `com.nianticlabs.pokemongo` e **Pokémon GO**, respectivamente. Outras instalações e aplicativos existentes no aparelho não devem ser modificados.

## Identidade de assinatura definitiva

Certificado SHA-256 do PGS: `D9:5C:6B:DF:CB:D9:1D:C5:C9:CD:E6:98:48:7C:88:E4:99:47:71:A4:75:E4:EF:DE:45:67:B8:D5:F4:4E:96:CF`.

Este certificado deve permanecer constante. Os segredos de assinatura estão no GitHub Actions, **não** no repositório. Nunca gere uma segunda JKS para atualizar o PGS. O build falha se a assinatura não corresponder.

## Versões Android

| PGS | Jogo base | Android `versionCode` |
| --- | --- | ---: |
| v0.3.8-pgs.2 | Pokémon GO 0.439.0 | 2026111602 |
| **v0.3.8-pgs.3** | Pokémon GO 0.439.0 | **2026111603** |
| **v0.0.1** | Pokémon GO 0.439.0 | **2026111604** |
| **v0.0.2 (candidata)** | Pokémon GO 0.439.0 | **2026111605** |

O último código de build PGS verificado é registrado em [`pgrazor/PGS_LAST_VERSION_CODE`](../pgrazor/PGS_LAST_VERSION_CODE). Para cada novo release completo, `pgrazor/release_apk.py` usa `max(codigo_do_jogo, ultimo_pgs+1)` antes de assinar o APK não-root, mantendo o `game_version_code` original para verificar a compatibilidade do módulo Root. O valor realmente assinado é acrescentado ao `build-info.json` em `apk_version_code`.

**Após concluir e verificar cada novo APK assinado**, atualize `PGS_LAST_VERSION_CODE` com o `apk_version_code` do release anterior *antes* de compilar a seguinte. A geração de updates pontuais também pode usar `pgrazor/pgs_update.py`, que valida APK fonte, assinatura, package, alteração única no manifesto e assinatura de saída.

## Verificação antes de distribuir

1. Confira `packageName=com.nianticlabs.pokemongo`, o certificado PGS e `versionCode` maior ou igual à versão instalada.
2. Verifique assinatura com `apksigner verify --print-certs`, integridade ZIP e alinhamento com `zipalign`.
3. Preserve os dados do usuário; nunca oriente uma desinstalação como procedimento normal de atualização.
4. Confirme instalação e login em dispositivo real. Uma compilação aprovada **não** comprova funcionamento do jogo.

A versão v0.3.8-pgs.3 foi gerada e assinada em [GitHub Actions #45963966748](https://github.com/LucianoToscano/PGS/actions/runs/45963966748), com SHA-256 `1e42c50f84afe5edf9570dfa808ba5e4be99b64d3ae28199b7316981c7414d4c`. É uma versão inicial limpa para quem já desinstalou a antiga. Não foi testada no aparelho do usuário.

## Proteção do caminho de release completo

O código `pgrazor/release_apk.py` agora distingue o PGS pelo seu ledger `PGS_LAST_VERSION_CODE`: exige a variável `PGRAZOR_KEYSTORE` apontando para a chave existente, gera `PGS.apk` e rejeita o binário se o SHA-256 do certificado não for o definido para PGS. Se o ledger PGS não existir, o processo é **bloqueado**; não será gerado um instalador com identificação externa com a assinatura PGS.

O workflow herdado `Android release (non-root and rooted)` está **explicitamente bloqueado no repositório PGS**, porque ainda usa o mecanismo de distribuição legado e não deve publicar pacotes com nomes ou segredos de assinatura misturados. A candidata atual PGS v0.0.2 usa o workflow próprio `.github/workflows/pgs-v0.0.2-release.yml`, validado para gerar APK completo com os controles Java recompilados, mantendo os demais arquivos do APK anterior por hash. O bloqueio não modifica nem elimina o instalador v0.3.8-pgs.3 já assinado.

Os testes automatizados cobrem a recusa de chaves ausentes, de `versionCode` inválido e de certificados divergentes. **Eles não substituem a validação de uma build completa e sua instalação física.**

## Nova linha pública de versões PGS

A primeira versão pública independente é `v0.0.1`. O nome de distribuição solicitado é `PGS v0.0.1.apk`; a geração interna segura continua usando `PGS.apk` antes de renomear a cópia verificada para o release. O Android identifica o app pelo pacote `com.nianticlabs.pokemongo`, não pelo nome do arquivo.

O APK `v0.3.8-pgs.3` tem `versionCode=2026111603`. O primeiro release completo `v0.0.1` deve usar `versionCode >= 2026111604`, mantendo o mesmo certificado. A versão visível do PGS (`v0.0.1`) não equivale à versão do jogo-base (`0.439.0`) e não substitui o `versionCode` Android.

A partir de `v0.0.1`, o atualizador consulta **somente** os releases do repositório `LucianoToscano/PGS`, valida a entrada de arquivo versionada e exige o SHA-256 correspondente antes de encaminhar ao instalador Android. O antigo APK não recebe essa configuração retroativamente: o primeiro upgrade desta linha requer a instalação manual do novo APK por cima da instalação PGS compatível.

Sem evidência de teste físico, uma build só pode ser marcada como **candidata ou draft**, nunca como instalação e gameplay confirmados.

## Nomes de arquivos do GitHub e continuidade futura

O arquivo no artefato Actions tem o nome solicitado `PGS v0.0.1.apk`. Ao anexar um APK ao GitHub Release, o próprio GitHub normaliza espaços em nomes de assets para pontos: `PGS.v0.0.1.apk`. O atualizador PGS verifica esse **nome real de release**, a URL do repositório `LucianoToscano/PGS` e o checksum SHA-256 da lista de release antes da instalação. Os nomes externos não alteram o package Android nem a chave.

A candidata PGS v0.0.1 foi verificada com o certificado definitivo e o Android `versionCode=2026111604`. O ledger de continuidade registra esse código para que a próxima build use **2026111605 ou maior**. A versão pública seguinte deverá ser `v0.0.2`, mediante nova compilação e testes; o registro do ledger não significa que a instalação física já foi testada.

O release v0.0.1 permanece em **draft** até confirmação real de instalação e login. As verificações automatizadas comparam as entradas originais do APK e preservam integralmente as bibliotecas nativas e outros DEX do jogo, exceto o controle Java PGS atualizado e o `versionCode`.

## Candidata v0.0.2 — rebranding incorporado ao APK

A reconstrução da `v0.0.2` usa **somente** o APK completo e assinado `v0.0.1`, confirmado com SHA-256 `23c0c4e9f9e87676038856e76b16613c91bf4bbd04a5c8cc9eb4f317d6926ef4` (Actions #45973576985). Atualiza o DEX PGS e o campo interno da versão, mantendo o restante dos arquivos do jogo integralmente igual, verificado por hashes de cada entrada. Nenhum download do APKMirror é efetuado. O novo `versionCode=2026111605` impede regressão; a próxima geração deverá usar código **2026111606 ou maior**.

O novo workflow `.github/workflows/pgs-v0.0.2-release.yml` produz `PGS v0.0.2.apk` e os recibos verificáveis, exigindo o certificado PGS permanente, package `com.nianticlabs.pokemongo` e jogo-base `0.439.0`. O fluxo antigo de `v0.0.1` fica arquivado e não pode recompilar automaticamente a versão antiga. O GitHub Release de `v0.0.2` é criado **somente como rascunho** até testes em aparelho real.

O símbolo interno e o joystick são mantidos exatamente como na base anterior. A conta Ko-fi do projeto original foi removida das opções de patrocínio PGS, sem configurar uma conta substituta não autorizada.
