# PGS AUTO SYNC — monitoramento upstream

O workflow `PGS AUTO SYNC` consulta somente a referência pública `refs/heads/main` do repositório de origem identificado no arquivo [NOTICE](../NOTICE), sem baixar ou executar código ou APKs, sem escrever no repositório e sem mesclar alterações. Quando a revisão muda, consulta também os metadados da comparação pública: commits, resumo por mensagem, arquivos, adições/remoções, caminhos locais correspondentes e áreas prioritárias. A lista de commits ou arquivos pode ser limitada pela API; o relatório sinaliza isso e não afirma conflitos sem revisão humana. O resumo do GitHub Actions registra a revisão consultada e se requer revisão humana. Uma revisão diferente não implica que seja descendente da anterior.

## Ativação

- Execução manual: Actions → PGS AUTO SYNC → Run workflow, após integração na main.
- Agendamento: habilitado por padrão, diariamente às 10:17 UTC (07:17 em Brasília/Fortaleza). Configure `PGS_AUTO_SYNC_ENABLED=false` para desativar o agendamento; a execução manual e a verificação após mudança do próprio workflow na main continuam disponíveis.
- `PGS_UPSTREAM_REVIEWED_SHA`: opcional; SHA de 40 caracteres da última revisão efetivamente auditada. Se ausente, usa a base original importada.
- Nenhum segredo, API paga ou permissão de escrita é necessário. A execução está sujeita às regras e cotas do GitHub Actions; não habilitar serviços pagos.

## Interpretação

`unchanged`: SHA igual à referência auditada. `review_required`: SHA diferente, precisa de análise em branch independente. Falhas de rede e referências inválidas falham o job, sem inventar resultados. Não alterar a revisão auditada até concluir a revisão. Este monitor não verifica versões do Pokémon GO, não integra alterações automaticamente e não publica artefatos.


## English

Read-only monitoring of the original public repository recorded in NOTICE. It queries the main ref, compares the reviewed SHA, and reports whether review is needed. Manual execution is available; daily scheduled checks are enabled by default. Set PGS_AUTO_SYNC_ENABLED=false to disable the schedule. Changes to the workflow on main trigger a verification run. For changed revisions, the report includes bounded public comparison metadata, commit-message category hints, changed files and local path review candidates. API truncation is flagged; no merge conflicts are claimed. No source download, branch write or merge is performed.
