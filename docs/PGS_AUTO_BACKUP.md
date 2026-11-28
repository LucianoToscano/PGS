# PGS AUTO BACKUP

Cria uma cópia temporária do código-fonte rastreado na main, usando as regras de exclusão do `tools/source_bundle.py`. Não recebe Secrets, não modifica branches e não inclui histórico Git, APKs ou chaves de assinatura. As regras de exclusão são preventivas e não substituem revisão de conteúdo sensível antes de commits.

## Uso

Após integração, execute Actions → PGS AUTO BACKUP → Run workflow → main. Para permitir a execução semanal aos domingos às 11:43 UTC (08:43 em Fortaleza), configure `PGS_AUTO_BACKUP_ENABLED=true`; deixe ausente ou false para desativar o agendamento. Não depende de API paga; observe as cotas do GitHub Actions.

## Arquivos

- `PGS-source-tools.zip`: snapshot de fonte e ferramentas.
- `SHA256SUMS.txt`: hash SHA-256, verificado antes do upload.
- `SOURCE_COMMIT.txt`: commit exato do snapshot.

O artefato permanece disponível por 14 dias. Baixe uma cópia para armazenamento próprio se precisar de retenção maior. O ZIP não substitui backup completo de Git, credenciais, releases ou armazenamento externo. Para verificar uma cópia em Linux, use `sha256sum -c SHA256SUMS.txt` na pasta dos três arquivos. Não restaure sobre uma árvore de trabalho com alterações locais.


## English

The optional weekly job and manual run archive tracked source only, verify the ZIP and SHA-256, record the exact commit, and retain the artifact for 14 days. Set the repository variable to true only to enable the scheduled run. It is not a complete Git/release/credential backup.
