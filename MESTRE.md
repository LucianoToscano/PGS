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

## Inventário confirmado

CI [45913909515](https://github.com/LucianoToscano/PGS/actions/runs/45913909515), job `140228458429`: 734 arquivos com correspondências (incluindo histórico). Contagens ativas por categoria: namespace Java 615; variáveis legadas 414; identificadores nativos 1863; caminhos 435; marca 358. As categorias podem se sobrepor; não equivalem a tarefas ou arquivos distintos. Histórico permanece preservado.

## Fila

- [x] Validar e integrar preflight de configuração.
- [x] Inventário inicial validado pelo CI. Execute `python -B tools/pgs_identity_inventory.py --json` para relatório por arquivo.
- [ ] Validar migração do ID do aplicativo de prévia para `dev.pgs.preview` e nome `pgs-preview.apk`. Classes Java, runtime e identificadores de produção permanecem inalterados.
- [ ] Migrar os demais identificadores técnicos em lotes coordenados; preservar contratos de compatibilidade.
- [ ] Configurar credenciais próprias de assinatura e entrada autorizada; não copiar valores secretos para o Git ou chat.
- [ ] Validar CI e preparar testes de compatibilidade autorizados.
- [ ] Planejar monitoramento de versões e upstream sem baixar ou publicar conteúdo não autorizado; automação desativada até aprovação.
- [ ] Revisar melhorias legadas individualmente, com evidência e testes.

## Regras

Trabalhar em branches independentes; registrar commit-base; validar CI antes de integração por PR. Não confundir testes de código com validação no aparelho. Não publicar artefatos ou acionar anúncios sem autorização. Não gerar cobranças. Não declarar APK pronto sem evidência de compilação e verificação.
