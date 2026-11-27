# PGS — controle da reconstrução

## Base e preservação

- Upstream: jpitty03/PGRazor, commit `1106592aa045759f55f594ff6968f783ff636fe9`.
- Backup original: `backup/pgrazor-original`.
- PGBR continua independente; não alterar seu nome, histórico ou automações por esta migração.
- Preservar LICENSE e atribuição upstream. Não alterar registros de evidência histórica.

## Integrações confirmadas até este lote

| PR | Escopo | Status |
| --- | --- | --- |
| #1 | Identidade inicial e site | Integrada |
| #2 | Identidade inicial Android | Integrada |
| #3 | Versão 0.00.01 e canal próprio de releases | Integrada |
| #4 | Nomes dos artefatos PGS | Integrada |
| #5 | Isolamento de anúncios Discord | Integrada em `fa525bd638a037cfab58708395e7545527f0e422` |
| #6 | Preflight de configuração e MESTRE.md | Integrada em `3f18312872b92f83300b30e4ba19c9807974b303` |
| #7 | Inventário técnico | Integrada em `d5c39c4db149784b1644eaf2d9da72b5a99314c6` |
| #8 | AUTO SYNC inicial | Integrada em `1863a9d66c1339143c0db29665cfbb9c1d696c42` |
| #9 | Identidade da prévia Android | Integrada em `646aae7b2e5acc706a8a4925d78fdd38ac801e0e` |
| #10 | Verificador de configuração e notas iniciais | Integrada em `7ff567c7aacf005b9ea813ceeb41b48e267dfe8a` |
| #11 | AUTO BACKUP inicial | Integrada em `ef94f379155970f7b2270d598f35e40acab1c334` |

| #12 | Validação de pacote e assinatura da prévia | Integrada em `de515d2d396c99fa8aa6c91308aca69b14ffb8f8` |

## Inventário confirmado

CI [45913909515](https://github.com/LucianoToscano/PGS/actions/runs/45913909515), job `140228458429`: 734 arquivos com correspondências (incluindo histórico). Contagens ativas por categoria: namespace Java 615; variáveis legadas 414; identificadores nativos 1863; caminhos 435; marca 358. As categorias podem se sobrepor; não equivalem a tarefas ou arquivos distintos. Histórico permanece preservado.

## Fila

- [x] Validar e integrar preflight de configuração.
- [x] Inventário inicial validado pelo CI. Execute `python -B tools/pgs_identity_inventory.py --json` para relatório por arquivo.
- [x] Migração da identidade da prévia integrada e validada pelo CI; teste físico pendente. Classes Java, runtime e identificadores de produção permanecem inalterados.
- [ ] Migrar os demais identificadores técnicos em lotes coordenados; preservar contratos de compatibilidade.
- [ ] Configurar credenciais próprias de assinatura e entrada autorizada; não copiar valores secretos para o Git ou chat.
- [ ] Validar CI e preparar testes de compatibilidade autorizados.
- [x] AUTO SYNC inicial integrado; execução real e agendamento ainda não confirmados.
- [ ] Monitoramento de versões do jogo separado, sem download ou publicação não autorizados.
- [x] Verificador de configuração e notas iniciais integrados; execução manual do diagnóstico pendente.
- [x] AUTO BACKUP inicial integrado; execução do workflow específico ainda pendente.
- [x] Compilação CI da prévia `pgs-preview.apk` confirmada no [run 45929853563](https://github.com/LucianoToscano/PGS/actions/runs/45929853563); não é o jogo.
- [x] Verificação de assinatura, ID e hash da prévia aprovada no [run 45931132488](https://github.com/LucianoToscano/PGS/actions/runs/45931132488). Upload opcional não executado; nenhum APK jogável produzido.
- [ ] Validar AUTO DEV inicial: classificação automática de alterações em PRs, sem modificar ou mesclar código.
- [ ] Revisar melhorias legadas individualmente, com evidência e testes.

## Regras

Trabalhar em branches independentes; registrar commit-base; validar CI antes de integração por PR. Não confundir testes de código com validação no aparelho. Não publicar artefatos ou acionar anúncios sem autorização. Não gerar cobranças. Não declarar APK pronto sem evidência de compilação e verificação.
