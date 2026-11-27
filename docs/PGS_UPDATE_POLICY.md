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
| **v0.0.3 (candidata assinada)** | Pokémon GO 0.439.0 | **2026111606** |
| **v0.0.4 (candidata planejada)** | Pokémon GO 0.439.0 | **2026111607** |

O último código de build PGS verificado é registrado em [`pgs/PGS_LAST_VERSION_CODE`](../pgs/PGS_LAST_VERSION_CODE). Para cada novo release completo, `pgs/release_apk.py` usa `max(codigo_do_jogo, ultimo_pgs+1)` antes de assinar o APK não-root, mantendo o `game_version_code` original para verificar a compatibilidade do módulo Root. O valor realmente assinado é acrescentado ao `build-info.json` em `apk_version_code`.

**Após concluir e verificar cada novo APK assinado**, atualize `PGS_LAST_VERSION_CODE` com o `apk_version_code` do release anterior *antes* de compilar a seguinte. A geração de updates pontuais também pode usar `pgs/pgs_update.py`, que valida APK fonte, assinatura, package, alteração única no manifesto e assinatura de saída.

## Verificação antes de distribuir

1. Confira `packageName=com.nianticlabs.pokemongo`, o certificado PGS e `versionCode` maior ou igual à versão instalada.
2. Verifique assinatura com `apksigner verify --print-certs`, integridade ZIP e alinhamento com `zipalign`.
3. Preserve os dados do usuário; nunca oriente uma desinstalação como procedimento normal de atualização.
4. Confirme instalação e login em dispositivo real. Uma compilação aprovada **não** comprova funcionamento do jogo.

A versão v0.3.8-pgs.3 foi gerada e assinada em [GitHub Actions #45963966748](https://github.com/LucianoToscano/PGS/actions/runs/45963966748), com SHA-256 `1e42c50f84afe5edf9570dfa808ba5e4be99b64d3ae28199b7316981c7414d4c`. É uma versão inicial limpa para quem já desinstalou a antiga. Não foi testada no aparelho do usuário.

## Proteção do caminho de release completo

O código `pgs/release_apk.py` agora distingue o PGS pelo seu ledger `PGS_LAST_VERSION_CODE`: exige a variável `PGS_KEYSTORE` apontando para a chave existente, gera `PGS.apk` e rejeita o binário se o SHA-256 do certificado não for o definido para PGS. Se o ledger PGS não existir, o processo é **bloqueado**; não será gerado um instalador com identificação externa com a assinatura PGS.

O workflow de publicação upstream e os workflows antigos de recompilação PGS estão explicitamente desativados nas fontes atuais. As implementações originais e os registros das compilações permanecem no histórico Git. Os pacotes assinados anteriormente não foram alterados.

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

A compilação histórica v0.0.2 produziu um APK completo assinado e recibos de verificação, com certificado PGS permanente, package `com.nianticlabs.pokemongo` e jogo `0.439.0`. O release existente permanece em rascunho. A execução verificada é https://github.com/LucianoToscano/PGS/actions/runs/45980315394; o artefato de Actions tem prazo de expiração.

O símbolo interno e o joystick são mantidos exatamente como na base anterior. A conta Ko-fi do projeto original foi removida das opções de patrocínio PGS, sem configurar uma conta substituta não autorizada.

## Validação atual do candidato completo

Os quatro workflows históricos de publicação/recompilação são bloqueios explícitos, somente leitura. Para validar a próxima candidata completa, abra [Validação PGS v0.0.4](https://github.com/LucianoToscano/PGS/actions/workflows/pgs-build.yml), selecione `main` e confirme `authorized_input` somente se tiver autorização para usar a entrada de jogo verificada por hash e o certificado existente. Por padrão, a execução envia somente recibos, não um APK para download nem release público. O verificador exige nomes de artefatos PGS por padrão; conjuntos arquivados exigem `--legacy-names`. Package instalado, certificado e ledger de releases permanecem inalterados.

### Configuração privada obrigatória

A execução anterior v0.0.3 46047731065 falhou pela ausência da URL de entrada então obrigatória. Esse mecanismo histórico foi substituído pela busca autorizada do rascunho no mesmo repositório, descrita abaixo. Os segredos de assinatura existentes continuam obrigatórios.

A prévia independente de testes passa a usar `dev.pgs.preview`. É uma instalação Android separada do pacote anterior; os dados da prévia antiga não são migrados automaticamente e o pacote anterior não é desinstalado. Identidades do jogo e do instalador Root permanecem inalteradas. A limpeza reconhece recibos históricos de prévia. Os exemplos de configuração do feed usam o caminho PGS para novas implantações; o endpoint de produção permanece inalterado até verificação independente.

### Entrada autorizada no repositório existente

Use no PGS o modelo de anexo de release do PGBR: crie um **rascunho não publicado** com a tag `build-inputs` e, somente se houver autorização para armazenar o pacote original do jogo, anexe `Pokemon_GO_0.439.0_ARM64_ORIGINAL.apkm` (169083658 bytes, SHA-256 `c6d3c04c38ca2f2446957633b4fee8c93dcc9cebdbbaddc9cb9651722ef8f54f`). Nunca publique esse rascunho. Um rascunho em repositório público não equivale a um repositório privado. Se a autorização exigir armazenamento efetivamente privado, use uma solução privada aprovada; não envie o arquivo aqui. O job manual de validação usa seu token efêmero e `tools/pgs_pinned_input.py` para conferir rascunho exato, estado do anexo, tamanho, digest e hash do arquivo baixado, e reconferir o rascunho. Apenas esse job precisa de `contents: write` para acessar rascunhos; a permissão abrange o job inteiro, não apenas uma etapa. O checkout não persiste credenciais. O script não altera releases, não baixa de outro repositório, não publica nem envia arquivos do jogo. `PGS_INPUT_URL` e tokens externos de entrada deixam de ser obrigatórios no workflow candidato. Os aliases de assinatura existentes são preservados; a chave é carregada somente após verificação do arquivo, e o workflow envia apenas recibos de validação por padrão. O mantenedor deve criar o rascunho e fornecer a entrada autorizada. A CI de código e o monitor permanecem somente leitura, exceto o job de notificações por issues já existente. O monitor não baixa pacotes, não promove perfis nem dispara builds assinados automaticamente.

### Retenção opcional e autorizada da candidata

A primeira build completa v0.0.3 (Actions 46054404520, código d4eb3192c505ea53e8c072cefc1703f604c21122) passou na validação estática com SHA-256 do APK `e9cae313bd3d98087ed370e211c690857c2acb18973f740faf1c814d86dda225`, 185818917 bytes, versionCode 2026111606 e o certificado existente. O APK temporário foi apagado; apenas os dois recibos foram preservados. Testes físicos e de atualização por cima ainda estão pendentes.

Por padrão, o workflow continua enviando somente recibos. Se o mantenedor tiver autorização para conservar a candidata modificada e assinada neste rascunho não publicado do GitHub, marque explicitamente `authorized_input` e `retain_authorized_candidate` em main. A etapa opcional recompila e verifica independentemente o APK, remove a chave temporária e cria um novo rascunho não publicado `v0.0.3`, contendo somente `PGS.v0.0.3.apk`, `PGS.json`, `build-info.json` e `SHA256SUMS.txt`. Confere os digests dos anexos e o commit de origem; não envia o APKM original, não modifica `build-inputs`, não sobrescreve candidatos, não publica releases nem avança o ledger da versão instalada. Rascunho parcial ou conflitante exige revisão do mantenedor; não publique. O hash da nova compilação poderá diferir do registro histórico. A candidata assinada ainda não foi homologada em dispositivo nem aprovada para distribuição. Um rascunho em repositório público não equivale a repositório privado; use armazenamento privado aprovado se a autorização exigir isso. Nenhum APK é exposto por artefatos públicos de Actions.


### Preparação da candidata v0.0.4

O rascunho assinado v0.0.3 foi preservado pela execução [46057980490](https://github.com/LucianoToscano/PGS/actions/runs/46057980490), commit `004a0fa584da8fac35661aa28ff3c2622746864a`, SHA-256 do APK `4dcc5408070732de2241facafd2e624531f56ad99382aa22f1d06dcbe8277843`. O ledger registra o último código de candidata assinada verificada `2026111606`, sem declarar homologação física ou publicação. O workflow sucessor prepara `v0.0.4`, código `2026111607`, em um novo rascunho não utilizado, mantendo a assinatura existente. Ambas as autorizações continuam explícitas e os rascunhos anteriores permanecem intactos. A descrição de retenção anterior é o registro histórico da v0.0.3. Nenhum APK v0.0.4 ou teste físico é declarado antes de execução bem-sucedida.


## Compilação assinada permanente por solicitação

O [PGS AUTO BUILD](https://github.com/LucianoToscano/PGS/actions/workflows/pgs-build.yml) substitui o workflow por versão. É acionado por alteração de `build-request.json` integrada à `main` canônica ou nova tentativa manual explicitamente autorizada. A solicitação inicial desativada evita uma segunda build v0.0.4 enquanto termina a execução existente 46070917440. Não há assinatura em pushes comuns, PRs ou solicitações desativadas.

Para a próxima versão patch solicitada, confirme a candidata anterior assinada e registre versão e código Android em `pgs/VERSION` e `pgs/PGS_LAST_VERSION_CODE`. No mesmo commit revisado, configure schema 1, enabled e authorized_input como true apenas quando autorizado, version seguinte, previous_version_code, previous_apk_sha256, game_version, game_version_code e input_sha256 fixados no perfil, e retain_authorized_candidate booleano explícito. A validação confere alteração da solicitação no commit exato, repositório e branch canônicos, incremento monotônico, recibo e digest do APK anterior e certificado existente antes dos testes completos e assinatura. A nova tentativa manual exige confirmações próprias; nenhum rascunho ou tag existente é sobrescrito. A saída permanece candidata não publicada com recibos de verificação, nunca distribuição pública automática. O ledger registra a última candidata verificada, não versão futura não comprovada. Envie apenas uma solicitação de cada vez. As descrições anteriores das execuções fixas v0.0.3/v0.0.4 são históricas.
