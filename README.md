# PGS

Projeto independente derivado de uma base de código aberto para Android. O PGS está em desenvolvimento, com alterações incrementais, testes de código e identidade própria.

## Estado do projeto

- Base original preservada; mudanças revisadas separadamente.
- Monitor de versões estáveis do Pokémon GO no catálogo público do APKMirror, com consulta diária às 09h23 (horário de Brasília).
- Download automático de APKM desativado: o monitor consulta somente metadados.
- Ainda não há um APK jogável do PGS validado para publicação. O pacote de código-fonte não é um instalador. Em testes internos e execuções manuais, o GitHub Actions pode disponibilizar `PGS-preview.apk`, uma prévia independente com assinatura de desenvolvimento, sem o jogo original. Não é uma versão jogável nem uma release de produção.

## Repositório e acompanhamento

- [GitHub Actions](https://github.com/LucianoToscano/PGS/actions): testes e monitoramento.
- [Issues](https://github.com/LucianoToscano/PGS/issues): acompanhamento do projeto.
- [Releases do PGS](https://github.com/LucianoToscano/PGS/releases): área destinada às futuras versões próprias.
- [Contribuições e verificações](CONTRIBUTING.md).

## Organização

| Pasta | Conteúdo |
| --- | --- |
| `.github/workflows/` | Verificações e automação do repositório |
| `docs/` | Documentação e histórico técnico |
| `pgrazor/` | Código herdado da base original |
| `tools/` | Verificações e empacotamento de código-fonte |
| `website/` | Código do site herdado |

Os nomes internos da base original são preservados durante a migração para evitar mudanças amplas e desnecessárias. Entradas de build, chaves privadas e dados locais não devem ser publicados.

## Créditos e licença

O PGS deriva de [PGRazor](https://github.com/jpitty03/PGRazor), cujo código original é disponibilizado sob a [licença MIT](LICENSE). Os avisos de autoria e as [licenças de terceiros](THIRD_PARTY.md) são preservados.

Pokémon GO e seus recursos não estão cobertos por essa licença. O PGS é independente e não tem vínculo com a publicadora do jogo.
