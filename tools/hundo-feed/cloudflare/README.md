# PGS Hundo Feed

## Português

O Worker lê feeds compactos v1 autorizados. Use Workers Free, a pasta `tools/hundo-feed/cloudflare` e o comando `npx wrangler deploy`. O Wrangler provisiona o vínculo KV `FEED`. Configure `SOURCES` como variável JSON com uma lista de objetos. Cada objeto precisa de `name` (identificador curto), `url` (HTTPS terminado em /hundos.json) e `interval_s` (inteiro, mínimo 300). Use apenas fontes com permissão para coleta e redistribuição. A lista vazia não faz requisições externas. Não inclua tokens em URLs. O coletor Python permanece disponível no diretório pai.

O cron a cada cinco minutos grava 288 instantâneos simulados por dia e, com fontes ativas, até 288 instantâneos reais e 288 cópias de recuperação adicionais (864 gravações/dia no total) em operação normal. Falhas preservam os dados anteriores e aumentam o intervalo entre tentativas. Consulte /hundos.json para verificar o horário da última coleta bem-sucedida, contagens e estado de cada fonte. Antes da primeira coleta bem-sucedida, o serviço responde HTTP 503. Valide várias atualizações, compatibilidade no dispositivo e expiração antes de alterar o APK. Para recuperar a versão anterior do código, use o histórico de implantações do Worker. Uma reversão de código não restaura dados do KV.

## English

Use Workers Free with the project root `tools/hundo-feed/cloudflare` and deploy command `npx wrangler deploy`. Wrangler provisions the dedicated `FEED` KV binding. Set `SOURCES` to a JSON array of authorized v1 feeds. Each entry requires a short `name`, an HTTPS `url` ending in /hundos.json, and integer `interval_s` of at least 300 seconds. Confirm automated collection and public redistribution rights first. An empty list performs no upstream requests. Keep credentials out of URLs. The original Python service is available in the parent directory.

A five-minute cron writes 288 simulated snapshots per day plus up to 288 production snapshots and 288 recovery copies with sources enabled (864 writes/day total) in normal operation. Failures retain prior rows and extend the retry interval. Inspect /hundos.json for the last successful source timestamp, source counts and status. Before the first successful poll the endpoint returns HTTP 503. Verify successive updates, expiry and on-device compatibility before changing the APK. Use Worker deployment history for code rollback. Rolling back code does not restore KV data.

## Validação e permissões / Verification and permissions

- PT-BR — A rota `/simulation/hundos.json` usa apenas dados sintéticos, identifica a simulação no JSON e exerce Cron, KV, filtragem e leitura HTTPS. Execute `node worker.test.mjs` para os testes locais. O endpoint principal retorna 503 sem uma fonte ativa e validada. Cada leitura do serviço consulta o KV. O cabeçalho de cache permite reutilização por 15 segundos.
- EN — The isolated `/simulation/hundos.json` route exercises Cron, KV, filtering and HTTPS with explicitly labelled synthetic data. Run `node worker.test.mjs` for local checks. Production returns 503 without an active, validated source. Each service read uses KV. The cache header permits reuse for 15 seconds.
- PT-BR — Em 27/11/2026 o endereço candidato da FaustusFoundry retornou um agregado com PoGoCoordinates. Os [termos de uso](https://pogocoordinates.com/terms) restringem a redistribuição em massa. As linhas compactas não identificam o fornecedor individual. O operador confirmou que a autorização específica do PGS abrange esses fornecedores. O agregado está configurado para consulta a cada cinco minutos e as cinco instâncias municipais a cada dez minutos. O intervalo de 300 segundos é uma decisão operacional do PGS. O fornecedor não informou cota.
- EN — On 2026-11-27 the candidate FaustusFoundry feed included PoGoCoordinates. Its [terms](https://pogocoordinates.com/terms) restrict bulk redistribution. Compact rows lack individual provider attribution. The operator confirmed project-specific permission covering the named providers. The aggregate is configured for five-minute polling and the five city instances for ten-minute polling. The 300-second interval is an operator setting. The provider has supplied no quota.

## Fontes e cobertura / Sources and coverage

| Provedor / Provider | Consulta / Query | Cobertura / Coverage |
| --- | --- | --- |
| FaustusFoundry | Compact v1, 5 min | Agregado; cada registro mantém o formato do APK. Aggregate provenance only. Alternate PGS path returned 404 on 2026-11-27. |
| NYC, SG, London, Sydney, Vancouver PokéMap | One city adapter, five instances, 10 min each | Only 15/15/15 spawns with known expiry. City sources may overlap the aggregate. |
| iFlowGo | One global search page plus one bounded nearby request, 10 min each | One provider. Pokémon: global page 1. Raids: Times Square, 2 km. No worldwide raid coverage claim. |
| PGSharp Free 100% IV | Candidate only · `pgsharp-free-100iv` · [identified service](https://f.pgsharp.com/peanuts) | Independent provider; zero verified records. No scheduled requests. |
| Moonani / PokeList | Public v2 sample | A 2 km species-25 query at Times Square returned an empty list. Zero confirmed records. |
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
