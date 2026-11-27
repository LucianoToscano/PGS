# Monitor diário de versões oficiais do Pokémon GO

O monitor do PGS consulta **somente o catálogo público de metadados** do APKMirror, uma vez ao dia (12:23 UTC). Não baixa APKs, não altera o jogo, não dispara builds e não publica releases.

## Origem da versão de referência

A versão aprovada do PGS é lida de `pgs/native/schema/game/current.json` por `tools/game_update.py`. Em 27/11/2026, a base é **0.439.0**. Isso evita que o monitor fique inativo quando nenhuma variável do GitHub estiver configurada.

Opcionalmente, a variável do repositório `PGS_GAME_REVIEWED_VERSION` pode elevar a referência, mas não reduzi-la abaixo do perfil versionado. A variável não aprova uma atualização técnica nem altera o APK.

## Notificações no GitHub

Se o catálogo apresentar uma versão estável mais recente que a referência, o workflow `PGS AUTO UPDATE - Version monitor` cria uma issue com o título `PGS ALERTA: Pokemon GO X.Y.Z`, atribuída ao proprietário do repositório. Antes de criar, pesquisa issues abertas e fechadas para evitar alertas duplicados por versão. O job de notificação tem concorrência serializada.

O alerta significa **apenas** que uma versão apareceu no catálogo público; não comprova disponibilidade universal, compatibilidade com os offsets/hooks atuais nem funcionamento em dispositivo.

## Testes e operação

O código é `tools/pgs_version_monitor.py`, originalmente preparado nas branches de desenvolvimento do PGS e agora integrado à `main`. Os testes locais não precisam de rede:

```bash
python -B tools/pgs_version_monitor.py --self-test
python -B -m unittest tools/test_pgs_version_monitor.py -v
```

Também são executados por `tools/check.py` na CI. O workflow executa testes offline em PRs e, em agendamentos ou execução manual, realiza a consulta pública e cria uma issue somente quando necessário.

Para consultar manualmente depois da integração, abra **GitHub → Actions → PGS AUTO UPDATE - Version monitor → Run workflow**. Nenhum segredo de assinatura é necessário. O resultado da consulta aparece no resumo da execução.

Uma falha de acesso ao catálogo deve produzir **erro visível**, não ser interpretada como ausência de novas versões. O monitor não deve contornar bloqueios do serviço nem realizar downloads.
