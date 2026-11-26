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

## Fila

- [x] Validar e integrar preflight de configuração.
- [ ] Inventariar referências técnicas antes de migrar caminhos, namespaces e bibliotecas; não substituir em massa. Ferramenta de inventário adicionada nesta branch, aguardando CI. Execute `python -B tools/pgs_identity_inventory.py --json` para relatório por arquivo, sem conteúdo ou valores de Secrets.
- [ ] Configurar credenciais próprias de assinatura e entrada autorizada; não copiar valores secretos para o Git ou chat.
- [ ] Validar CI e preparar testes de compatibilidade autorizados.
- [ ] Planejar monitoramento de versões e upstream sem baixar ou publicar conteúdo não autorizado; automação desativada até aprovação.
- [ ] Revisar melhorias legadas individualmente, com evidência e testes.

## Regras

Trabalhar em branches independentes; registrar commit-base; validar CI antes de integração por PR. Não confundir testes de código com validação no aparelho. Não publicar artefatos ou acionar anúncios sem autorização. Não gerar cobranças. Não declarar APK pronto sem evidência de compilação e verificação.
