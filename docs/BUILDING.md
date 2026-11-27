# Compilação, assinatura e instalação do PGS

Este guia cobre apenas os instaladores **PGS — Pokémon GO Spoofers**. O código usa algumas interfaces técnicas de compatibilidade, mas a identidade pública e os releases pertencem ao repositório https://github.com/LucianoToscano/PGS.

## Candidata atual

| Campo | Valor |
|---|---|
| PGS | **v0.0.2** (candidata) |
| Jogo-base | Pokémon GO `0.439.0` (ARM64) |
| Nome instalado | **Pokémon GO** |
| Package | `com.nianticlabs.pokemongo` |
| Android `versionCode` | `2026111605` |
| Certificado SHA-256 | `D9:5C:6B:DF:CB:D9:1D:C5:C9:CD:E6:98:48:7C:88:E4:99:47:71:A4:75:E4:EF:DE:45:67:B8:D5:F4:4E:96:CF` |
| APK de distribuição | `PGS v0.0.2.apk` |
| Asset do release | `PGS.v0.0.2.apk` |
| SHA-256 do APK | `91865f6242519091a771617f962f17620405624a4a56addec0909d2cdf6b68c1` |

**Workflow da versão:** https://github.com/LucianoToscano/PGS/actions/workflows/pgs-v0.0.2-release.yml

**Build completa verificada:** https://github.com/LucianoToscano/PGS/actions/runs/45980315394

Não confunda um ZIP de código ou APK de prévia com o jogo completo.

## Testes do código-fonte

Execute no ambiente de desenvolvimento configurado:

```sh
python -B tools/check.py
```

O CI também executa testes nativos em Linux e compila os controles Android no ambiente do GitHub Actions. Os catálogos de idioma, regras de atualização, política de assinatura e regressões de comportamento fazem parte dos testes.

## Compilação dos controles

O projeto continua usando um diretório técnico de origem compatível com o runtime já instalado. A compilação de controles pode ser acionada por:

```sh
python -B pgs/build.py
```

Este comando depende de JDK e Android SDK compatíveis. O arquivo de preview gerado **não** é um instalador completo nem substitui o jogo. O arquivo completo deve ser produzido pelo workflow dedicado da versão, combinando os controles compilados com o APK-base autorizado e executando a verificação de todas as entradas.

## Assinatura obrigatória

A assinatura usa exclusivamente a **chave PGS existente**. Nunca crie outra chave para um APK distribuído e nunca publique valores dos Secrets, senhas ou chaves privadas.

O workflow exige os segredos de assinatura PGS já configurados, verifica a assinatura final, o mesmo package e o crescimento de `versionCode`. Uma compilação de prévia assinada por chave de desenvolvimento não deve ser distribuída como versão funcional.

A política completa está em [PGS_UPDATE_POLICY.md](PGS_UPDATE_POLICY.md). O próximo APK após `v0.0.2` deve usar `versionCode` de pelo menos `2026111606`.

## Publicação segura

1. Faça a alteração em branch e execute testes automatizados.
2. Use o workflow dedicado PGS para compilar o **APK completo**.
3. Confirme `PGS.json`, `SHA256SUMS.txt`, tamanho do APK, assinatura, package e versão do jogo.
4. Prepare um **GitHub Release em rascunho**; só publique depois de confirmar instalação e login no celular.
5. Teste a atualização **por cima** do PGS anterior, sem desinstalar, para verificar a preservação dos dados.

O atualizador do aplicativo consulta exclusivamente os releases do repositório PGS e procura o asset GitHub com o nome normalizado `PGS.vX.Y.Z.apk`, conferindo o SHA-256 antes da instalação.

## Compatibilidade

O package Android permanece `com.nianticlabs.pokemongo`, o nome instalado permanece **Pokémon GO**, e o certificado continua o mesmo. Bibliotecas nativas, símbolos de ligação Java/JNI e preferências existentes só podem ser renomeados em uma migração específica com testes de atualização e backup.

O menu interno e o joystick são preservados nesta fase. Outras instalações e projetos no aparelho não devem ser tocados.

Um APK compilado e assinado **não comprova** automaticamente instalação, login nem funcionamento físico.

### Entrada autorizada no repositório existente

Use no PGS o modelo de anexo de release do PGBR: crie um **rascunho não publicado** com a tag `build-inputs` e, somente se houver autorização para armazenar o pacote original do jogo, anexe `Pokemon_GO_0.439.0_ARM64_ORIGINAL.apkm` (169083658 bytes, SHA-256 `c6d3c04c38ca2f2446957633b4fee8c93dcc9cebdbbaddc9cb9651722ef8f54f`). Nunca publique esse rascunho. Um rascunho em repositório público não equivale a um repositório privado. Se a autorização exigir armazenamento efetivamente privado, use uma solução privada aprovada; não envie o arquivo aqui. O job manual de validação usa seu token efêmero e `tools/pgs_pinned_input.py` para conferir rascunho exato, estado do anexo, tamanho, digest e hash do arquivo baixado, e reconferir o rascunho. Apenas esse job precisa de `contents: write` para acessar rascunhos; a permissão abrange o job inteiro, não apenas uma etapa. O checkout não persiste credenciais. O script não altera releases, não baixa de outro repositório, não publica nem envia arquivos do jogo. `PGS_INPUT_URL` e tokens externos de entrada deixam de ser obrigatórios no workflow candidato. Os aliases de assinatura existentes são preservados; a chave é carregada somente após verificação do arquivo, e o workflow envia apenas recibos de validação por padrão. O mantenedor deve criar o rascunho e fornecer a entrada autorizada. A CI de código e o monitor permanecem somente leitura, exceto o job de notificações por issues já existente. O monitor não baixa pacotes, não promove perfis nem dispara builds assinados automaticamente.

### Retenção opcional e autorizada da candidata

A primeira build completa v0.0.3 (Actions 46054404520, código d4eb3192c505ea53e8c072cefc1703f604c21122) passou na validação estática com SHA-256 do APK `e9cae313bd3d98087ed370e211c690857c2acb18973f740faf1c814d86dda225`, 185818917 bytes, versionCode 2026111606 e o certificado existente. O APK temporário foi apagado; apenas os dois recibos foram preservados. Testes físicos e de atualização por cima ainda estão pendentes.

Por padrão, o workflow continua enviando somente recibos. Se o mantenedor tiver autorização para conservar a candidata modificada e assinada neste rascunho não publicado do GitHub, marque explicitamente `authorized_input` e `retain_authorized_candidate` em main. A etapa opcional recompila e verifica independentemente o APK, remove a chave temporária e cria um novo rascunho não publicado `v0.0.3`, contendo somente `PGS.v0.0.3.apk`, `PGS.json`, `build-info.json` e `SHA256SUMS.txt`. Confere os digests dos anexos e o commit de origem; não envia o APKM original, não modifica `build-inputs`, não sobrescreve candidatos, não publica releases nem avança o ledger da versão instalada. Rascunho parcial ou conflitante exige revisão do mantenedor; não publique. O hash da nova compilação poderá diferir do registro histórico. A candidata assinada ainda não foi homologada em dispositivo nem aprovada para distribuição. Um rascunho em repositório público não equivale a repositório privado; use armazenamento privado aprovado se a autorização exigir isso. Nenhum APK é exposto por artefatos públicos de Actions.
