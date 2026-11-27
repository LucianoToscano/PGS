# PGS Hundo Feed

## English

Use Workers Free with the project root `tools/hundo-feed/cloudflare` and deploy command `npx wrangler deploy`. The collector clamps legacy backoff values to a 30-minute cap, honours `Retry-After`, strips a UTF-8 BOM before decoding, normalizes unambiguous numeric strings and publishes per-source diagnostics (`state`, `http_status`, `content_type`, `received`, `validated`, `discarded`, `next_retry`) in `/status.json`. Wrangler provisions the dedicated `FEED` KV binding. Set `SOURCES` to a JSON array of authorized v1 feeds. Each entry requires a short `name`, an HTTPS `url` ending in /hundos.json, and integer `interval_s` of at least 300 seconds. Confirm automated collection and public redistribution rights first. An empty list performs no upstream requests. Keep credentials out of URLs. The original Python service is available in the parent directory.

A five-minute cron writes up to 288 production snapshots and 288 recovery copies with sources enabled (576 writes/day total) in normal operation. Synthetic fixtures are offline tests only. Failures retain prior rows and extend the retry interval. Inspect /hundos.json for the last successful source timestamp, source counts and status. Before the first successful poll the endpoint returns HTTP 503. Verify successive updates, expiry and on-device compatibility before changing the APK. Use Worker deployment history for code rollback. Rolling back code does not restore KV data.

## Português

O Worker lê feeds compactos v1 autorizados. A recuperação de falhas usa teto de 30 minutos entre tentativas (respeitando `Retry-After`), a decodificação remove BOM UTF-8, strings numéricas inequívocas são normalizadas e `/status.json` publica diagnósticos por fonte (`state`, `http_status`, `content_type`, `received`, `validated`, `discarded`, `next_retry`). Use Workers Free, a pasta `tools/hundo-feed/cloudflare` e o comando `npx wrangler deploy`. O Wrangler provisiona o vínculo KV `FEED`. Configure `SOURCES` como variável JSON com uma lista de objetos. Cada objeto precisa de `name` (identificador curto), `url` (HTTPS terminado em /hundos.json) e `interval_s` (inteiro, mínimo 300). Use apenas fontes com permissão para coleta e redistribuição. A lista vazia não faz requisições externas. Não inclua tokens em URLs. O coletor Python permanece disponível no diretório pai.

O cron a cada cinco minutos grava, com fontes ativas, até 288 instantâneos reais e 288 cópias de recuperação (576 gravações/dia no total) em operação normal. Dados sintéticos ficam exclusivamente nos testes offline. Falhas preservam os dados anteriores e aumentam o intervalo entre tentativas. Consulte /hundos.json para verificar o horário da última coleta bem-sucedida, contagens e estado de cada fonte. Antes da primeira coleta bem-sucedida, o serviço responde HTTP 503. Valide várias atualizações, compatibilidade no dispositivo e expiração antes de alterar o APK. Para recuperar a versão anterior do código, use o histórico de implantações do Worker. Uma reversão de código não restaura dados do KV.

## Validação e permissões / Verification and permissions

- PT-BR — Execute `node worker.test.mjs` para os testes offline. O endpoint principal retorna 503 sem uma fonte ativa com coleta bem-sucedida. Respostas GET públicas ficam 15 segundos no cache de borda. Não há mais gravação periódica de simulação nem rota pública de simulação.
- EN — Run `node worker.test.mjs` for offline tests. Production returns 503 without an active source with a successful poll. Public GET responses are cached at the edge for 15 seconds. Synthetic snapshots are no longer written on schedule or publicly served.
- PT-BR — Em 27/11/2026 o endereço candidato da FaustusFoundry retornou um agregado com PoGoCoordinates. Os [termos de uso](https://pogocoordinates.com/terms) restringem a redistribuição em massa. As linhas compactas não identificam o fornecedor individual. O operador confirmou que a autorização específica do PGS abrange esses fornecedores. O agregado está configurado para consulta a cada cinco minutos e as cinco instâncias municipais a cada dez minutos. O intervalo de 300 segundos é uma decisão operacional do PGS. O fornecedor não informou cota.
- EN — On 2026-11-27 the candidate FaustusFoundry feed included PoGoCoordinates. Its [terms](https://pogocoordinates.com/terms) restrict bulk redistribution. Compact rows lack individual provider attribution. The operator confirmed project-specific permission covering the named providers. The aggregate is configured for five-minute polling and the five city instances for ten-minute polling. The 300-second interval is an operator setting. The provider has supplied no quota.

## Fontes e cobertura / Sources and coverage

| Provedor / Provider | Consulta / Query | Cobertura / Coverage |
| --- | --- | --- |
| FaustusFoundry | Compact v1, 5 min | Agregado; cada registro mantém o formato do APK. Aggregate provenance only. Alternate PGS path returned 404 on 2026-11-27. |
| NYC, SG, London, Sydney, Vancouver PokéMap | One city adapter, five instances, 10 min each | Endpoints online and schema-verified (see `DIAGNOSIS_2026-11-27.md`); the Worker currently receives a non-JSON body and reports `invalid_response`. City records also arrive via the authorized FaustusFoundry aggregate. No anti-bot bypass is implemented. |
| iFlowGo | IV-index search (`min_iv=100`), paginated, 10 min | Provider's IV index (`candidate_source=iv_index`); every page up to 8 is fetched atomically. Only 15/15/15 with exact coordinates and valid expiry; zero verified records before, ~100 100%-IV candidates per cycle. No raid requests. |
| PGSharp Free 100% IV | Candidate only · `pgsharp-free-100iv` · [identified service](https://f.pgsharp.com/peanuts) | Independent provider; zero verified records. No scheduled requests. |
| GOCoords (dormant) | Public 10-hundo feed, adapter shipped but NOT enabled | `https://gocoords.com/api/spawns` verified live 2026-11-27 (real rows, iv=100). Awaits operator permission attestation for redistribution; enable via `SOURCES` entry (see `DIAGNOSIS_2026-11-27.md` addendum). |
| Moonani / PokeList | [IV100 table](https://moonani.com/PokeList/), 15 min | Página inicial mostrou 217 registros; amostra 15/15/15 com coordenadas e expiração. Worker requests the first 100 rows via the existing table contract. The separate v2 NYC species-25 query returned zero. One provider across both endpoints. |
| PoGoCoordinates / LivePokéMap | Existing operator-account Python adapters | Direct collection needs operator credentials. The Worker does not use third-party accounts. |
| ARSpoofing / WeCatch / PokeCoords | Public validation | ARSpoofing returned 403 for snipe and nests. WeCatch timed out. No validated PokeCoords response. |
| PoGoMap.info | Public map | Web interface available; no confirmed machine-readable feed in this review. |
| PkmSpawn / PSSnipeFeeder / PoracleNG / RocketMap / ReactMap / Golbat / Aegis | Integration software | Requires a running instance or configured webhook. Repository URLs are not live data sources. |

PT-BR — O escopo do Worker é exclusivamente o Shundo Sniper: `/hundos.json` contém somente Pokémon selvagens declarados 100% IV, com coordenadas exatas e expiração futura, no formato compacto v:1. Os conectores que fornecem IV por atributo exigem 15/15/15; IV desconhecido ou contraditório é descartado. A consulta iFlowGo usa a página de Pokémon já homologada e filtra os resultados imediatamente, sem armazenar registros de outros IVs. Não há filtro remoto de IV presumido. As rotas públicas de Pokémon genéricos, Raids e simulação retornam 404. A API preserva somente as rotas auxiliares de status, fontes e administração protegida. Os dados de versões antigas no KV são filtrados nas leituras e nas próximas gravações.

EN — The Worker is scoped to the Shundo Sniper: `/hundos.json` contains only source-confirmed perfect-IV wild Pokémon, exact coordinates and valid expiry in compact v1 format. Adapters with individual IVs require 15/15/15. iFlowGo reads the existing bounded Pokémon page and discards non-hundos before storage; no unverified upstream IV parameter is invented. General Pokémon, raids and simulation routes return 404. Status, sources and authenticated administration remain. Legacy KV category records are excluded on reads and removed on subsequent snapshot writes.

### PGSharp Free 100% IV

PT-BR — A autorização declarada pelo operador já está registrada. O [estudo do PGBR](https://github.com/LucianoToscano/PGBR/blob/main/docs/PGSHARP_FREE_FEED_KEY_DESIGN_2026-11-22.md) identificou o serviço e separou a modalidade Free da Standard. A política e o diálogo existentes não implementam o transporte externo. O cofre protege a licença pessoal no aparelho. O material consultado não especifica o método HTTP de terceiros, o formato de resposta, a autenticação de servidor, os limites ou os termos de republicação pelo Worker. A homologação depende de um contrato do fornecedor e de uma amostra verificável com IV, coordenadas e expiração. Não atribuir ao PGSharp resultados de outros provedores.

EN — The operator's authorization is recorded. The [official feature list](https://www.pgsharp.com/features/) describes the product. PGBR's policy, dialog and Android key vault do not establish a server API. Activate only after verifying the provider's request and response contract, authentication, limits, redistribution scope and a real sample. Personal device licenses stay on the device. Candidate entries do not contribute to source counts.

`/status.json` — Estado das conexões e até 288 amostras de disponibilidade. A cópia KV `pgs-feed-backup-v1` permite recuperação do instantâneo anterior e passa pelos mesmos filtros de fontes e expiração. / Connection state and up to 288 availability samples. The previous KV snapshot is used when the current key is missing and passes the same source and expiry filters.

## Diagnóstico de 2026-11-27 / 2026-11-27 diagnosis

See `DIAGNOSIS_2026-11-27.md` for the per-source investigation with live evidence, root causes and the corrections applied in this revision.

## Production verification / Homologação

2026-11-27, 14:15 Fortaleza. The public v1 response contained 63 encounters and 93 spots. FaustusFoundry contributed 65 unique rows. Moonani contributed 91 of 94 active rows. The five city instances each returned a response that could not be decoded as JSON. Before the hundo-only scope change, iFlowGo had delivered 25 Pokémon and 108 raids on the now-retired category routes. These were historical observations, not hundo counts. Counts are observations at a point in time.

Em 27/11/2026 às 14h15 de Fortaleza, a coleta confirmou 156 registros únicos de Hundos. A disponibilidade dos dados varia conforme a expiração. Os cinco mapas regionais estavam sem JSON válido. A autorização já declarada para esses mapas continua registrada.

- [Hundos](https://pgs-hundo-feed.lucianotoscano.workers.dev/hundos.json)
- [Providers / Fontes](https://pgs-hundo-feed.lucianotoscano.workers.dev/sources.json) · [Status](https://pgs-hundo-feed.lucianotoscano.workers.dev/status.json)

**Administration.** The read-only `/admin` JSON report requires HTTP Basic authentication over HTTPS. Configure the Workers secret `ADMIN_PASSWORD` with a unique ASCII password in the Cloudflare dashboard and use username `admin`. Until configured, the route returns 503. Manage intervals and provider activation through reviewed changes to the Worker configuration. The per-location limit is 600 requests per 60 seconds for public routes and a separate bucket for admin.

**Administração.** O resumo `/admin` usa autenticação própria e cache desativado. Cadastre uma senha exclusiva como segredo `ADMIN_PASSWORD` diretamente na Cloudflare e utilize o usuário `admin`. Configurações de fontes e intervalos são versionadas no GitHub. Métricas de consumo ficam no painel da Cloudflare.

**Enrichment / Enriquecimento.** PoGoAPI, PokéAPI, DittoBase, Leek Duck and PvPoke are candidates for metadata and event enrichment. OpenStreetMap and Overpass supply geographic context. Shungo, iPogo, Pokemod, MAD, RealDeviceMap, Fletchling and Koji are research or architecture references here. None is counted as a live instance by the PGS collector.
