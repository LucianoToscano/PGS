# Como contribuir com o PGS

**Idiomas:** [🇺🇸 English](CONTRIBUTING.md) · 🇧🇷 Português (Brasil)

Para desenvolver o site React e consultar seu workflow de GitHub Pages, veja [website/README.md](website/README.md). Alterações no site não publicam APK.

## Regras para pull requests

Faça cada PR tratar de **um recurso, uma correção ou uma tarefa de manutenção coerente**. Inclua os testes e a documentação pertinentes. Separe formatação ampla, atualização de dependências e refatorações sem relação com o problema.

Antes de solicitar revisão:

- Descreva problema, comportamento anterior e resultado esperado. Para bugs, inclua passos de reprodução e vincule a issue relevante.
- Explique decisões técnicas, impacto na compatibilidade e limitações conhecidas. Para mudanças visuais, inclua capturas sem dados privados.
- Registre mudanças no app sob **Unreleased** no [CHANGELOG.md](CHANGELOG.md) e no [CHANGELOG.pt-BR.md](CHANGELOG.pt-BR.md), quando aplicável. Mudanças somente de site, testes ou ferramentas internas geralmente não exigem entrada de release.
- Atualize simultaneamente [README.md](README.md), [README.pt-BR.md](README.pt-BR.md) e os guias afetados. Não anuncie funcionalidades experimentais como se já estivessem publicadas.
- Inclua testes de regressão para alterações de comportamento, incluindo falhas e cancelamentos. Documentação e ajustes cosméticos pequenos não precisam de testes artificiais.
- Execute verificações relevantes e informe comandos e resultados exatos. Distinga testes automáticos, compilação e observações reais em um dispositivo.
- Revise o diff para evitar mudanças não relacionadas, arquivos gerados, dados pessoais e código obsoleto.

Use o modelo de pull request. CI aprovado não comprova funcionamento no jogo. Versões e releases são responsabilidade dos mantenedores.

## Validação

Para mudanças no código, execute:

```sh
python -B tools/check.py
```

Mudanças Android também exigem `python -B pgrazor/build.py`. Alterações nativas precisam de testes adequados e, quando disponível, verificação em Android ou MuMu. Informe versão do jogo e cenários testados. Quando não houver dispositivo, registre essa limitação explicitamente.

Para alterações no site, consulte [website/README.md](website/README.md): compilação e testes de navegador. Para documentação, confira links, comandos e coerência com a implementação.

## Regras do repositório e do runtime

Não envie APKs ou recursos privados do jogo, chaves de assinatura, logs privados, dados de contas nem coordenadas pessoais. Preserve procedência e avisos legais de terceiros. O empacotador de código rejeita arquivos privados indevidamente versionados.

Alterações nativas devem preservar leases, gerenciamento de memória, cancelamento, tratamento de erros e a integridade do mapa. Automações destrutivas devem manter regras de proteção e não atuar em inventários reais durante testes.

Use **PGS** nos nomes exibidos. O namespace Java atual `dev.pgrazor` continua preservado por compatibilidade binária até uma migração testada. Preserve a API pública `Control` e as chaves de preferências. Compatibilidade com uma nova versão do jogo precisa de contratos atualizados e testes explícitos no dispositivo.

A publicação de APK é uma operação do mantenedor, não de PR. Consulte [docs/pt-BR/BUILDING.md](docs/pt-BR/BUILDING.md).

## Como acrescentar ou separar um recurso

Mantenha os dois READMEs atualizados na mesma PR. Revise descrições e guias do site quando o recurso mudar.

- Comece por [arquitetura](docs/ARCHITECTURE.md) e [manutenibilidade](docs/MAINTAINABILITY.md); preserve os limites entre política, interface e código nativo.
- Cada módulo deve ter dependências explícitas e responsabilizar-se por timers, hooks e objetos retidos. A construção não pode inicializar classes do jogo fora da thread correta.
- O gameplay de produção usa código Java/nativo compilado. Scripts antigos de pesquisa permanecem em `pgrazor/runtime/bundles.json`, não devem retornar como runtime de produção.
- Nomeie testes Python como `test_*.py` e testes Node como `*-test.cjs`. Testes Java precisam de um runner mapeado no CI.
- Prefira testes pela API do módulo, evitando refatorar em massa junto a mudanças de comportamento.
- Informe resultados de compilação, testes de fixture e observações físicas separadamente.

Para atualizações do jogo, siga [docs/GAME_UPDATES.md](docs/GAME_UPDATES.md). Atualize o perfil da versão e regenere os cabeçalhos cobertos, revisando também bindings mantidos manualmente; um match de assinatura sozinho não prova compatibilidade.

O CI ainda define os aliases `PGRAZOR_BUILD_TOOLS=36.0.0` e `PGRAZOR_ANDROID_PLATFORM=android-36`. Para novas compilações locais, prefira `PGS_BUILD_TOOLS=36.0.0` e `PGS_ANDROID_PLATFORM=android-36`; as variáveis antigas continuam aceitas. A versão usa `PGS_VERSION` (ou o alias `PGRAZOR_VERSION`), com prioridade para o nome PGS. Essas opções NÃO alteram as variáveis de assinatura: não recrie chaves nem mude o identificador Android.

## Idiomas da documentação

O inglês é o idioma principal para títulos de PRs, issues, commits, releases e documentos canônicos. Português brasileiro tem versões correspondentes para README, changelog, contribuição e guias essenciais de compilação, atualização e idiomas. Atualize os dois idiomas juntos.

O site oferece seletor EN/PT-BR, separado da internacionalização do aplicativo Android (`pgrazor/i18n/`). Preserve nomes de arquivos, comandos, hashes, códigos Android, URLs e a licença original exatamente como estão.
