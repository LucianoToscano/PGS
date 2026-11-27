# PGS Hundo Feed

## English

Use Workers Free with the project root `tools/hundo-feed/cloudflare` and deploy command `npx wrangler deploy`. Wrangler provisions the dedicated `FEED` KV binding. Set `SOURCES` to a JSON array of authorized v1 feeds. Each entry requires a short `name`, an HTTPS `url` ending in /hundos.json, and integer `interval_s` of at least 300 seconds. Confirm automated collection and public redistribution rights first. An empty list performs no upstream requests. Keep credentials out of URLs. The original Python service is available in the parent directory.

A five-minute cron writes 288 simulated snapshots per day plus up to 288 production snapshots and 288 recovery copies with sources enabled (864 writes/day total) in normal operation. Failures retain prior rows and extend the retry interval. Inspect /hundos.json for the last successful source timestamp, source counts and status. Before the first successful poll the endpoint returns HTTP 503. Verify successive updates, expiry and on-device compatibility before changing the APK. Use Worker deployment history for code rollback. Rolling back code does not restore KV data.

## Português

O Worker lê feeds compactos v1 autorizados. Use Workers Free, a pasta `tools/hundo-feed/cloudflare` e o comando `npx wrangler deploy`. O Wrangler provisiona o vínculo KV `FEED`. Configure `SOURCES` como variável JSON com uma lista de objetos. Cada objeto precisa de `name` (identificador curto), `url` (HTTPS terminado em /hundos.json) e `interval_s` (inteiro, mínimo 300). Use apenas fontes com permissão para coleta e redistribuição. A lista vazia não faz requisições externas. Não inclua tokens em URLs. O coletor Python permanece disponível no diretório pai.

O cron a cada cinco minutos grava 288 instantâneos simulados por dia e, com fontes ativas, até 288 instantâneos reais e 288 cópias de recuperação adicionais (864 gravações/dia no total) em operação normal. Falhas preservam os dados anteriores e aumentam o intervalo entre tentativas. Consulte /hundos.json para verificar o horário da última coleta bem-sucedida, contagens e estado de cada fonte. Antes da primeira coleta bem-sucedida, o serviço responde HTTP 503. Valide várias atualizações, compatibilidade no dispositivo e expiração antes de alterar o APK. Para recuperar a versão anterior do código, use o histórico de implantações do Worker. Uma reversão de código não restaura dados do KV.

## Validação e permissões / Verification and permissions

- PT-BR — A rota `/simulation/hundos.json` usa apenas dados sintéticos, identifica a simulação no JSON e exerce Cron, KV, filtragem e leitura HTTPS. Execute `node worker.test.mjs` para os testes locais. O endpoint principal retorna 503 sem uma fonte ativa e validada. Respostas GET públicas ficam 15 segundos no cache de borda. Uma leitura fora desse cache consulta o KV. O cabeçalho de cache permite reutilização por 15 segundos.
- EN — The isolated `/simulation/hundos.json` route exercises Cron, KV, filtering and HTTPS with explicitly labelled synthetic data. Run `node worker.test.mjs` for local checks. Production returns 503 without an active, validated source. Public GET responses are cached at the edge for 15 seconds. Cache misses read KV. The cache header permits reuse for 15 seconds.
- PT-BR — Em 27/11/2026 o endereço candidato da FaustusFoundry retornou um agregado com PoGoCoordinates. Os [termos de uso](https://pogocoordinates.com/terms) restringem a redistribuição em massa. As linhas compactas não identificam o fornecedor individual. O operador confirmou que a autorização específica do PGS abrange esses fornecedores. O agregado está configurado para consulta a cada cinco minutos e as cinco instâncias municipais a cada dez minutos. O intervalo de 300 segundos é uma decisão operacional do PGS. O fornecedor não informou cota.
- EN — On 2026-11-27 the candidate FaustusFoundry feed included PoGoCoordinates. Its [terms](https://pogocoordinates.com/terms) restrict bulk redistribution. Compact rows lack individual provider attribution. The operator confirmed project-specific permission covering the named providers. The aggregate is configured for five-minute polling and the five city instances for ten-minute polling. The 300-second interval is an operator setting. The provider has supplied no quota.

## Fontes e cobertura / Sources and coverage

| Provedor / Provider | Consulta / Query | Cobertura / Coverage |
| --- | --- | --- |
| FaustusFoundry | Compact v1, 5 min | Agregado; cada registro mantém o formato do APK. Aggregate provenance only. Alternate PGS path returned 404 on 2026-11-27. |
| NYC, SG, London, Sydney, Vancouver PokéMap | One city adapter, five instances, 10 min each | Only 15/15/15 spawns with known expiry. City sources may overlap the aggregate. |
| iFlowGo | One global search page plus one bounded nearby request, 10 min each | One provider. Pokémon: global page 1. Raids: Times Square, 2 km. No worldwide raid coverage claim. |
| PGSharp Free 100% IV | Candidate only · `pgsharp-free-100iv` · [identified service](https://f.pgsharp.com/peanuts) | Independent provider; zero verified records. No scheduled requests. |
| Moonani / PokeList | [IV100 table](https://moonani.com/PokeList/), 15 min | Página inicial mostrou 217 registros; amostra 15/15/15 com coordenadas e expiração. Worker requests the first 100 rows via the existing table contract. The separate v2 NYC species-25 query returned zero. One provider across both endpoints. |
| PoGoCoordinates / LivePokéMap | Existing operator-account Python adapters | Direct collection needs operator credentials. The Worker does not use third-party accounts. |
| ARSpoofing / WeCatch / PokeCoords | Public validation | ARSpoofing returned 403 for snipe and nests. WeCatch timed out. No validated PokeCoords response. |
| PoGoMap.info | Public map | Web interface available; no confirmed machine-readable feed in this review. |
| PkmSpawn / PSSnipeFeeder / PoracleNG / RocketMap / ReactMap / Golbat / Aegis | Integration software | Requires a running instance or configured webhook. Repository URLs are not live data sources. |

PT-BR — `/pokemon.json` e `/raids.json` publicam apenas registros reais válidos. Consultas a categorias sem registros validados não geram um catálogo fictício. O campo `source` identifica o provedor. Em `/hundos.json`, as contagens por origem são calculadas depois de filtrar expirados e comparar duplicatas. A rota de simulação nunca alimenta essas categorias.

EN — Pokémon and raid responses use separate routes and include only validated, unexpired records. Each item retains its provider. Hundo source counts report active and unique records after merging. Rare Pokémon, quests, rare candy, Rocket, nests, power spots, gyms and stops await confirmed category-specific records and contracts.

### PGSharp Free 100% IV

PT-BR — A autorização declarada pelo operador já está registrada. O [estudo do PGBR](https://github.com/LucianoToscano/PGBR/blob/main/docs/PGSHARP_FREE_FEED_KEY_DESIGN_2026-11-22.md) identificou o serviço e separou a modalidade Free da Standard. A política e o diálogo existentes não implementam o transporte externo. O cofre protege a licença pessoal no aparelho. O material consultado não especifica o método HTTP de terceiros, o formato de resposta, a autenticação de servidor, os limites ou os termos de republicação pelo Worker. A homologação depende de um contrato do fornecedor e de uma amostra verificável com IV, coordenadas e expiração. Não atribuir ao PGSharp resultados de outros provedores.

EN — The operator's authorization is recorded. The [official feature list](https://www.pgsharp.com/features/) describes the product. PGBR's policy, dialog and Android key vault do not establish a server API. Activate only after verifying the provider's request and response contract, authentication, limits, redistribution scope and a real sample. Personal device licenses stay on the device. Candidate entries do not contribute to source counts.

`/status.json` — Estado das conexões e até 288 amostras de disponibilidade. A cópia KV `pgs-feed-backup-v1` permite recuperação do instantâneo anterior e passa pelos mesmos filtros de fontes e expiração. / Connection state and up to 288 availability samples. The previous KV snapshot is used when the current key is missing and passes the same source and expiry filters.

## Production verification / Homologação

2026-11-27, 14:15 Fortaleza. The public v1 response contained 63 encounters and 93 spots. FaustusFoundry contributed 65 unique rows. Moonani contributed 91 of 94 active rows. The five city instances each returned a response that could not be decoded as JSON. iFlowGo had previously delivered 25 Pokémon and 108 raids on its separate category routes. Counts are observations at a point in time.

Em 27/11/2026 às 14h15 de Fortaleza, a coleta confirmou 156 registros únicos de Hundos. A disponibilidade dos dados varia conforme a expiração. Os cinco mapas regionais estavam sem JSON válido. A autorização já declarada para esses mapas continua registrada.

- [Hundos](https://pgs-hundo-feed.lucianotoscano.workers.dev/hundos.json) · [Pokémon](https://pgs-hundo-feed.lucianotoscano.workers.dev/pokemon.json) · [Raids](https://pgs-hundo-feed.lucianotoscano.workers.dev/raids.json)
- [Providers / Fontes](https://pgs-hundo-feed.lucianotoscano.workers.dev/sources.json) · [Status](https://pgs-hundo-feed.lucianotoscano.workers.dev/status.json)

**Administration.** The read-only `/admin` JSON report requires HTTP Basic authentication over HTTPS. Configure the Workers secret `ADMIN_PASSWORD` with a unique ASCII password in the Cloudflare dashboard and use username `admin`. Until configured, the route returns 503. Manage intervals and provider activation through reviewed changes to the Worker configuration. The per-location limit is 600 requests per 60 seconds for public routes and a separate bucket for admin.

**Administração.** O resumo `/admin` usa autenticação própria e cache desativado. Cadastre uma senha exclusiva como segredo `ADMIN_PASSWORD` diretamente na Cloudflare e utilize o usuário `admin`. Configurações de fontes e intervalos são versionadas no GitHub. Métricas de consumo ficam no painel da Cloudflare.

**Enrichment / Enriquecimento.** PoGoAPI, PokéAPI, DittoBase, Leek Duck and PvPoke are candidates for metadata and event enrichment. OpenStreetMap and Overpass supply geographic context. Shungo, iPogo, Pokemod, MAD, RealDeviceMap, Fletchling and Koji are research or architecture references here. None is counted as a live instance by the PGS collector.
