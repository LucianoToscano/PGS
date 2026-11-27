# Configurações do repositório PGS

[🇺🇸 English](../en/PGS_REPOSITORY_SETTINGS.md) · [🇧🇷 Português (Brasil)](PGS_REPOSITORY_SETTINGS.md)

## Descrição About — inglês

A descrição pública **About** é uma configuração administrativa do GitHub, separada do README. Use este texto:

> PGS — Pokémon GO Spoofers. Independent Android project with location controls, joystick, maps, and companion tools for Pokémon GO.

Abra https://github.com/LucianoToscano/PGS, clique na engrenagem/edição do quadro **About**, cole o texto e salve. No navegador do celular, pode ser necessário ativar **Site para computador**. A integração de código conectada não tem permissão administrativa para editar esse campo.

## Onde está o workflow Website?

**Nome do workflow:** Website. **Arquivo:** `.github/workflows/pages.yml`.

- [Abrir o workflow Website](https://github.com/LucianoToscano/PGS/actions/workflows/pages.yml)
- [Última execução verificada com sucesso #45990719478](https://github.com/LucianoToscano/PGS/actions/runs/45990719478)
- [Configurações do GitHub Pages](https://github.com/LucianoToscano/PGS/settings/pages)

A execução de **27/11/2026** concluiu **build e deploy com sucesso**. Execuções antigas com X vermelho permanecem no histórico, mas não são o estado do `main` atual. Na aba Actions do navegador, procure **Website** na barra lateral; no aplicativo móvel essa lista pode ficar oculta. Para executar manualmente, use **Run workflow** na interface web.

O seletor **EN / PT-BR** do site é independente dos idiomas disponíveis no aplicativo Android.

## Por que ainda aparecem nomes antigos na busca?

A árvore de código `pgrazor/`, o pacote Java `dev.pgrazor`, os caminhos de execução `assets/pgrazor`, interfaces nativas e algumas preferências antigas são **contratos de compatibilidade técnica**. O histórico Git e branches de backup também foram preservados. Renomear esses elementos sem migração testada pode impedir que o APK PGS abra ou recupere dados salvos.

A identidade pública e os links de atualização devem usar PGS. O texto exato de atribuição legal permanece. A migração dos identificadores internos está registrada na [issue #38](https://github.com/LucianoToscano/PGS/issues/38) e exige testes, package/certificado inalterados, APK completo assinado e atualização física sem perda de dados. Não apague backups ou testes históricos só para reduzir resultados na busca.

O aplicativo instalado continua **Pokémon GO**, com pacote `com.nianticlabs.pokemongo` e assinatura PGS definitiva.
