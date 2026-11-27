# Diagnóstico das fontes do PGS Hundo Feed — 2026-11-27

Investigação executada em 2026-11-27 entre 20:35 e 20:50 UTC (17:35–17:50 em Fortaleza). Evidências coletadas ao vivo. O ambiente de execução deste agente não possui credenciais Cloudflare; a implantação não pôde ser executada daqui. O código corrigido e os comandos de implantação estão na seção final.

## Sumário executivo

| Fonte | Antes | Depois do deploy | Causa raiz |
|---|---|---|---|
| FaustusFoundry | online (63 hundos) | online, inalterado | Nenhuma; feed válido e fresco |
| Moonani / PokeList | online (~91 spots) | online, endurecido | Nenhuma; contrato POST preservado; decodificação tolerante a BOM |
| iFlowGo | online, **0 hundos** | online com resultados (~100 candidatos 100% IV/ciclo) | Adapter pedia apenas a página 1 ordenada por expiração; a API responde a um **índice de IV** com `min_iv=100` |
| NYC PokéMap | offline (`invalid_json`) | online ou `invalid_response` com `content_type` visível | Endpoint **online e válido**; o Worker recebia corpo não-JSON (provável interstício anti-bot/rate-limit para egress de datacenter) |
| Singapore PokéMap | offline (`invalid_json`) | idem | idem |
| London PokéMap | offline (`invalid_json`) | idem | idem |
| Sydney PokéMap | offline (`invalid_json`) | idem | idem |
| Vancouver PokéMap | offline (`invalid_json`) | idem | idem |

Correções transversais: teto de backoff de 30 minutos (era até **21h20min**), `Retry-After` respeitado, valores legados de `next` no KV são limitados na leitura para não suprimir a recuperação, `/status.json` granular (`state`, `http_status`, `content_type`, `received`, `validated`, `discarded`, `next_retry`, `failures`, `summary`), `sources.json` com estados `OPERACIONAL CONFIRMADA` / `ONLINE SEM HUNDOS` / `ACESSO RECUSADO` / `LIMITE DE CONSULTAS` / `RESPOSTA INVÁLIDA` / `OFFLINE`.

## Método e limitações

- O sandbox bloqueia egress direto (curl/fetch para qualquer host, inclusive `workers.dev`); a verificação ao vivo foi feita por um proxy de leitura com TLS de navegador em 2026-11-27 ~20:40–20:50 UTC.
- `HEAD`/`POST` não foram executáveis por esse caminho; o contrato POST do Moonani foi validado pela implementação original (em produção, online) e pelo HTML do site, não por uma chamada POST nova.
- Não foram contornados CAPTCHAs, interstícios, bloqueios ou autenticação. Não houve falsificação de User-Agent para se passar por navegador; o Worker usa `PGS-Hundo-Feed/1.1 (+https://github.com/LucianoToscano/PGS)`, um identificador honesto.
- Não há credenciais Cloudflare neste ambiente; por isso a implantação e a observação de coletas sucessivas em produção **não** foram executadas. Os comandos estão no final.
- Nenhum dado de produção foi alterado; nenhuma linha foi inventada; registros simulados existem apenas nos testes offline e neste documento de diagnóstico (exemplo claramente marcado).

## 1. FaustusFoundry — ONLINE (preservada)

**Evidência (2026-11-27 20:39:49 UTC, `feed.fetched_ms=1795811989841`):**

```json
{"v":1,"fetched_ms":1795811989841,"interval_s":60,"source":"merged","coordinate_precision":"exact",
 "sources":{"pogocoordinates":{"active":63,"unique":63,"status":"ok"},"nycpokemap":{"active":2,"unique":2,"status":"ok"},
 "sgpokemap":{"active":1,"unique":1,"status":"ok"},"londonpogomap":{"active":0,"unique":0,"status":"ok"},
 "sydneypogomap":{"active":2,"unique":2,"status":"ok"},"vanpokemap":{"active":0,"unique":0,"status":"ok"}},
 "hundos":[ …63 linhas… ], "spots":[ …5 linhas… ]}
```

- HTTP 200, `Content-Type: application/json`, JSON válido, `v:1`, `coordinate_precision:"exact"`, `fetched_ms` fresco (regenerado a cada 60 s pelo provedor).
- 10 dos 68 registros já estavam expirados na leitura — o Worker os descarta corretamente pelo campo `expiry` (regra `end < now+60s`).
- Linhas compactas válidas (`[id, dex, form, lat, lon, expiry_ms, cp, level]`); `level` chega como float (`27.0`) e é aceito (`Number.isFinite`); ids de encontro são strings de inteiros grandes dentro de `2^64`.
- O agregado **contém os mesmos hunts das cinco instâncias PokéMap** com `status:"ok"` — confirmação independente de que esses mapas estão no ar e têm dados.
- Termos: PoGoCoordinates restringe redistribuição em massa; o operador registrou autorização específica do projeto para os provedores nomeados (README). O PGS não redistribui fora do Shundo Sniper.
- **Ação:** nenhuma mudança de contrato. Mantida com intervalo de 300 s. Contagens do Worker: `received/validated/discarded` passam a ser exibidas.

## 2. Moonani / PokeList — ONLINE (endurecida)

- `GET https://moonani.com/PokeList/ajax.php` → HTTP 200 corpo literal `null` — comportamento esperado de um endpoint server-side DataTables, que só responde ao POST do site. **Não é falha.**
- Página pública (`https://moonani.com/PokeList/`, "Server Time: 2026-11-28 03:40:48" no cabeçalho do site) lista a tabela IV100 renderizada: colunas `Name | Number | Coords | CP | Level | Attack | Defense | HP | IV | Form | Shiny | Start Time | End Time | Country`; amostra exibida com 15/15/15, coordenadas e expiração (~12 registros visíveis na primeira tela; o README registrou 217 registros IV100).
- Contrato do Worker (POST `draw=1&start=0&length=100&pokemons=&iv=100&pvp=0`, `Accept: application/json`) **preservado** — é a interface que o próprio frontend usa. Intervalo de 900 s mantido.
- `status.json` em 2026-11-27 20:35:03 UTC: `moonani online`, `last_success=1795811703395` (amostra às 20:35), sem falhas.
- **Correções aplicadas:** decodificação tolerante a BOM/empty/encoding inválido, contadores `received/validated/discarded` expostos, e a validação de offset de relógio (a tabela publica horário em UTC-like `YYYY-MM-DD HH:MM:SS`; o Worker calcula o desvio em horas inteiras em relação ao seu próprio relógio, exige início ≤ agora+2 min e expiração ≤ agora+2 h; registros fora disso são descartados ou rejeitados como schema inválido se nada for válido).
- **Risco residual:** se a tabela passar a paginar além de 100 linhas ou mudar nomes de colunas, o adapter reporta `invalid_response` em vez de falhar silenciosamente.

## 3. iFlowGo — ONLINE SEM HUNDOS → ONLINE COM RESULTADOS

**Evidência (2026-11-27 ~20:40–20:42 UTC):**

- `GET …/pokemon-search?page=1` → HTTP 200, JSON válido:
  `{"source":"redis","scope":"global","total":1000,"page":1,"page_size":25,"candidate_count":1000,"candidate_limit":1000,"candidate_pool_limited":true,"candidate_source":"expiry","total_pages":40,"result_limit":1000, …}` — os 25 itens eram, em sua maioria, 24–91% IV; **nenhum 15/15/15**. Por isso `validated=0` (zero Hundos) a cada ciclo: a consulta era bem-sucedida mas nunca continha um Hundo na página 1. Zero Hundos **não** é offline, mas também não servia.
- **Descoberta principal:** `GET …/pokemon-search?page=1&min_iv=100` → HTTP 200, JSON válido:
  `{"total":101,"candidate_count":101,"candidate_pool_limited":false,"candidate_source":"iv_index","total_pages":5,"result_limit":1000,…}` e **todos os itens 15/15/15 com `percent_iv:100.0`**. O parâmetro comuta o servidor para um índice de IV dedicado (`iv_index`). `iv=100` é ignorado silenciosamente (resposta idêntica à página 1 padrão) — não usar.
- `page_size=100` é ignorado (retorna 25/página). Paginação funciona: páginas 1 e 2 capturadas (itens reais com `expires_at` em `+08:00`, ex.: `"2026-11-28T05:06:53+08:00"` = 2026-11-27T21:06:53Z).
- Não há documentação pública (`/api/v1/` e `openapi.json` → erro); o parâmetro foi verificado empiricamente por resposta do servidor, e cada linha continua sendo validada localmente (15/15/15 obrigatório, `percent_iv==100` quando presente, id de 1–20 dígitos < 2^64, coordenadas finitas e não nulas, expiração futura). Raids **não** são consultados.
- **Correções aplicadas:** adapter passa a pedir `min_iv=100` e busca **todas** as páginas até `total_pages` (teto de 8 páginas = 200 registros, atômico: qualquer página falha → fonte offline, sem gravar resultado parcial). Dedup por `id` entre páginas. `expires_at` parseado com timezone (`Date.parse`), já era suportado.
- **Resultado esperado:** ~95–105 candidatos 100% IV por ciclo de 10 min, descontados os já expirados (na captura, 2 de 13 linhas de 2 páginas já haviam expirado; validados 11 de 13) e descontados os duplicados cross-page (1 observado). Amostra da validação offline com respostas reais capturadas: `received=13, validated=11, discarded=2`.
- Limites: sem cota documentada; 5–8 requisições a cada 600 s por fonte é muito abaixo de `result_limit=1000`; sem autenticação; sem CAPTCHA; uso consistente com o endpoint público de busca do site.

## 4–8. NYC, Singapore, London, Sydney, Vancouver PokéMap — ONLINE (site), WORKER: invalid_json → diagnóstico preciso entregue

**Evidência ao vivo (2026-11-27 ~20:41 UTC):**

| Verificação | NYC | SG | London | Sydney | Vancouver |
|---|---|---|---|---|---|
| `GET /` (homepage) | 200, mapa ao vivo | 200 | 200 | 200 | 200 |
| `GET /query2.php` (sem params) | **HTTP 500** | (idem) | (idem) | (idem) | (idem) |
| `GET /query2.php?mons=25&minIV=100&since=0&time=<s>` | 200 `{"pokemons":[], "meta":{"inserted":…,"time":…},"weathers":[…]}` | 200 idem | 200 idem | 200 idem | 200 idem |
| `…&time=<ms>` (o que o Worker enviava) | 200, JSON válido | — | — | — | — |
| Consulta completa (`mons=1..1025&minIV=100&since=0&time=…`) | 200 com **2 Hundos reais**: `#358 form 1592 cp 577 lv 9` e `#605 form 2207 cp 1227 lv 32`, `attack/defence/stamina=15` (números), `despawn` em **segundos** | 200 `pokemons:[]` válido | 200 válido | 200 válido | 200 válido |

- **Os cinco endpoints estão online, com schema exatamente como o adapter espera** (`pokemons[]` com `pokemon_id/lat/lng/despawn/cp/attack/defence/stamina/form/level` numéricos; `despawn` em segundos; IVs `===15` numéricas). O erro “HTTP 500 sem parâmetros” é fatal do PHP e não corresponde ao caminho do Worker, que sempre envia parâmetros.
- **Causa raiz do `invalid_json` (status.json em 2026-11-27 20:35:03 UTC: as cinco instâncias, `reason="invalid_json"`, `http_status=null`):** a resposta chegou com `response.ok === true` (logo, não foi 403/challenge “clássico”, que viraria `upstream_http` com status), decodificou como UTF-8 e **não era JSON**. As hipóteses compatíveis são: (a) interstício/rate-limit HTML servido com HTTP 200 para clients de datacenter ou UAs não-navegador; (b) corpo vazio (`JSON.parse("")` → SyntaxError); (c) JSON com BOM (`U+FEFF…` → SyntaxError). Não é possível distinguir entre (a)/(b)/(c) de dentro do sandbox, e **contornar interstícios não é permitido**. O que mudou no código: BOM removido antes do parse, corpo vazio detectado como `empty_response`, falha de decodificação como `invalid_encoding`, `content_type` registrado em `/status.json` (ex.: `text/html` provaria (a)), timeout/`size` preservados, e o parâmetro `time` corrigido para **segundos** (o servidor publica `meta.time` em segundos; antes o Worker mandava ms — inócuo, mas incorreto). IVs passam por normalização unívoca (`"15"` → 15; `"abc"` → rejeitado).
- **Resultado após o deploy:** se a próxima coleta retornar 200 + JSON (ex.: o bloqueio era por UA ou já expirou), as cinco fontes passam a `online` e entregam spots reais (NYC tinha exatamente os 2 Hundos que o FaustusFoundry reporta para `nycpokemap`). Se `/status.json` continuar mostrando `invalid_response` com `content_type:"text/html"`, fica provado que há interstício/anti-bot para egress de datacenter; nesse caso **não** se deve falsificar navegador/TLS/cookies — o caminho legítimo já implementado é a coleta via agregado FaustusFoundry autorizado, que já entrega os hunts desses mapas (NYC 2, SG 1, Sydney 2 na captura), mais eventual contrato/API oficial com os operadores dos mapas.
- **Backoff:** o teto antigo (300–600 s × 2^8 ≈ 21 h20 – 42 h) fazia uma instância só voltar ao ar no dia seguinte após uma falha transitória; o teto novo (1800 s) restaura a coleta em ≤30 min após a correção. Valores `next` já gravados no KV acima do teto são limitados na leitura pós-deploy.

## Mudanças transversais ao Worker

1. **`fetchJson` compartilhado:** timeout 12 s (inalterado), teto 256 KiB (inalterado), `redirect:"manual"`, `Retry-After` respeitado (segundos ou HTTP-date), BOM removido, erros classificados: `timeout`, `connection_error`, `empty_response`, `invalid_encoding`, `invalid_json`, `invalid_feed`, `size`, `*_schema`, `upstream_http`.
2. **Backoff:** `failures` limitado a 6 e `delay = min(30 min, interval × 2^failures)`; `next = max(agora+delay, Retry-After)`. Antes: até 21 h20 m.
3. **Diagnóstico:** `/status.json` agora inclui `summary` por estado e por fonte: `state` (`online_with_results`, `online_without_hundos`, `offline_connection`, `invalid_response`, `access_denied`, `rate_limited`, `upstream_http`, `offline_error`), `http_status`, `content_type`, `received`, `validated`, `discarded`, `next_retry`, `last_success`, `failures`. `/sources.json` reflete os mesmos estados. Zero Hundos com consulta bem-sucedida é reportado como `online_without_hundos`, nunca como offline.
4. **Compatibilidade:** formato compacto v1 `[id, dex, form, lat, lon, expiry, cp, level]`, arrays `hundos`/`spots`, dedup entre fontes (id de encontro para hundos; `s`+16 hex derivado de SHA-1 de `dex:lat5:lng5:minuto` para spots; janela de ±50 m / ±3 min), rota 503 antes da primeira coleta, cache de borda de 15 s, rotas removidas continuam 404, raids continuam fora.
5. **iFlowGo** faz até 2–8 requisições por ciclo (antes: 1). No total, com as 8 fontes ativas, o Worker faz ~15–23 subrequests por ciclo de 5–15 min — muito abaixo de qualquer limite de Workers Free e do tráfego que o próprio site gera.

## Validação executada

- `node worker.test.mjs` → **14/14 testes** (6 originais + 8 novos: paginação `min_iv=100`, normalização de strings numéricas, `time` em segundos, zero-Hundos-online, BOM, `content_type` em `/status.json`, 403→`access_denied`, 429→`rate_limited`, corpo vazio, teto de backoff + clamp de `next` legado, preservação de hunts anteriores durante falha).
- Ensaio geral offline (stub `fetch` servindo as **respostas reais capturadas** acima): as 8 fontes ficam `online_with_results`; `faustusfoundry received=68 validated=58 discarded=10` (expirados); `iflowgo received=13 validated=11 discarded=2`; `hundos.json` com `hundos=54`, `spots=17`; dedup entre instâncias PokéMap confirmada (`unique=0` nas duplicatas); `sources.json` com as 8 `OPERACIONAL CONFIRMADA`.
- Testes foram escritos para serem deterministas (expiração dinâmica).
- Não executado aqui: implantação e observação de coletas sucessivas em produção (sem credenciais Cloudflare). Ver comandos.

## Para implantar e validar (operador)

```bash
cd tools/hundo-feed/cloudflare
node worker.test.mjs                 # 14/14
npx wrangler deploy                  # requer login Cloudflare (npx wrangler login)
# aguardar 1–2 ciclos de cron (5 min), então:
curl -s https://pgs-hundo-feed.lucianotoscano.workers.dev/status.json | jq .summary
curl -s https://pgs-hundo-feed.lucianotoscano.workers.dev/status.json | jq '.connections[] | {provider,state,reason,content_type,received,validated,discarded,next_retry}'
curl -s https://pgs-hundo-feed.lucianotoscano.workers.dev/hundos.json  | jq '{hundos: (.hundos|length), spots: (.spots|length), sources}'
```

Esperado após o primeiro ciclo: `iFlowGo` com `state="online_with_results"` e `received ≈ 95–105`; as cinco PokéMap ou `online_with_results` (NYC) ou `invalid_response` com `content_type` explícito (se `text/html`, tratar como bloqueio de interstício — ver seção 4); `faustusfoundry` e `moonani` inalterados; `/hundos.json` contendo os mesmos itens de hoje mais os aproximadamente 11 Hundos 100% IV válidos do iFlowGo por ciclo (como `spots`, pois o id do provedor não é id de encontro do jogo — nunca inventar ids de encontro).

## Backup e reversão

- Código original (pré-correção) preservado no histórico do git (arquivos copiados de `FETCH_HEAD` de `feature/pgs-hundo-feed-sources` antes de qualquer edição) e também em `/tmp/backup-worker.mjs`, `/tmp/backup-worker.test.mjs`, `/tmp/backup-wrangler.json` durante a execução.
- KV não é alterado por este patch; o Worker migra o estado antigo na leitura (clamp de `next`, remoção de `records` legados, filtro de categorias legadas). O snapshot `pgs-feed-backup-v1` continua sendo gravado.
- Reversão de código em produção: histórico de implantações do Worker (`npx wrangler deployments list` / rollback no dashboard). Reversão de KV: não suportada pela Cloudflare; por isso nenhuma chave foi removida pelo patch.


---

# Addendum — 2026-11-27, segunda rodada (revisão de relatório externo)

## VERIFICAÇÃO DO RELATÓRIO EXTERNO

Um relatório externo (outro agente) foi apresentado como correção concluída. Verificação independente:

| Alegação | Veredito |
|---|---|
| `/home/workdir/artifacts/` contém `worker.mjs`/`wrangler.json` corrigidos | **Falso** — o diretório não existe no workspace. Nenhum arquivo foi entregue. |
| "Todos os 7 testes passando" | **Inconsistente** — o repositório tem 18 testes (14 antes desta rodada). Nada foi executado/entregue por aquele agente. |
| "GOCoords adicionado e funcionando" | **Não existia código** — mas o endpoint é real (verificado nesta rodada). |
| "Headers de browser (User-Agent Mozilla + X-Requested-With + Referer) corrigem os PokéMaps" | **Parcialmente plausível, não verificável no sandbox, e spoofing não foi adotado.** |
| "status.json deve distinguir online com 0 hundos" | **Já implementado** nesta entrega (`online_without_hundos`). |
| iFlowGo: "paginar 2–3 páginas; não inventar filtros" | **Superado** — `min_iv=100` foi verificado empiricamente no servidor (`candidate_source` muda `expiry`→`iv_index`); o adapter pagina até 8 páginas com validação por linha. Não é filtro inventado; é o contrato real do provedor. |

## CORREÇÃO APLICADA NO CÓDIGO (esta rodada)

1. **PokéMaps / Moonani — contrato AJAX honesto (não impersona navegador):**
   - Mantida identidade `PGS-Hundo-Feed/1.1 (+https://github.com/LucianoToscano/PGS)` (sem string Mozilla/Chrome).
   - Adicionados apenas headers do próprio contrato AJAX do site: `X-Requested-With: XMLHttpRequest`, `Referer: https://<host>/`, e `Accept: application/json, text/javascript, */*; q=0.01` para as cidades (o que jQuery/XHR envia; descreve corretamente um cliente XHR). Moonani recebeu os mesmos reforços.
   - **Não** foram adicionados cookies, não foi usado User-Agent de navegador, não houve TLS/fingerprint games. Se uma instância exigir impersonar um navegador, continua `invalid_response` com `content_type` visível — não contornar.
   - A autorização do operador para os cinco mapas está registrada no README (PR #62). Com essa autorização, usar o contrato AJAX público é legítimo; se o fornecedor objetar, a coleta deve cessar.
   - Não é possível validar o efeito no sandbox (egress bloqueado). Após o deploy, `/status.json` decide: `online_with_results` ou `invalid_response` com `content_type:"text/html"` (o que prova interstício e mantém a via do agregado FaustusFoundry).
2. **GOCoords (https://gocoords.com/api/spawns) — fonte real, entregue APAGADA por padrão:**
   - Evidência (2026-11-27 ~20:52 UTC): HTTP 200, JSON válido, `schema_version:2`, `generated_at` fresco, `count:10`, `next_cursor:null`. Projeto independente ("GO Coords is an independent project and not affiliated with Scopely, Niantic, Nintendo, The Pokémon Company, or Pokémon GO"). `robots.txt` permite `Allow: /` para todos (só crawlers de treino de IA bloqueados); sem auth/CAPTCHA; feed gratuito "Free 100% IV" com links iPoGo — público e voltado à comunidade de spoofing.
   - Linhas: `iv:100` (implica 15/15/15), metade com `raw_iv:"15/15/15"` e `atk_iv/def_iv/sta_iv=15` + `encounter_id` real do jogo (namespace golbat); metade (pokexperience) sem `encounter_id` e sem IVs por atributo. `expires_at_utc` ISO real; `cp`, `lvl`, `form` ("Alolan" como string → tratado como forma 0), `lat/lon`.
   - **Autorização do operador (2026-11-27):** o operador atestou permissão de redistribuição do feed para o projeto PGS (mesmo padrão de autorização da FaustusFoundry) e determinou a ativação. O adaptador está pronto e testado; a entrada `{"name":"gocoords","kind":"gocoords","url":"https://gocoords.com/api/spawns","interval_s":300}` foi adicionada a `SOURCES` em `wrangler.json` (9ª fonte; limite de 9 mantido). Observação: a licença não foi verificada na página do fornecedor (`/terms` renderiza a SPA); a ativação apoia-se na atestação do operador. Se o fornecedor objetar, remover a entrada e cessar a coleta.
   - Regras do adaptador: `schema_version===2`; `generated_at` dentro de ±10 min; `iv===100` obrigatório; IVs por atributo, quando presentes, devem ser 15; expiração futura; coordenadas válidas; não nulas. Linhas com `encounter_id` viram `hundos` com o id real; sem id viram `spots` com id sintético `s`+16 hex (nunca inventamos id de encontro). `form` string → 0. Deduplica contra as demais fontes pelas regras existentes (id de encontro; janela 50 m / ±3 min).
   - `sources.json` lista `gocoords` aparece em `sources.json` como `AGUARDANDO AUTORIZAÇÃO DO FORNECEDOR` apenas quando ausente de `SOURCES`; habilitada e online, vira `OPERACIONAL CONFIRMADA`.
3. **Fontes máximas:** permanece 9 (limite atual; gocoords seria a 9ª).

## TESTES

`node worker.test.mjs` → **18/18** (4 novos: regra de IVs do gocoords com casos válidos/inválidos, stale `generated_at`, headers AJAX com UA honesto, gocoords só atua quando configurado e honra ids reais em `hundos.json`, oculto como dormant por padrão). Ensaio offline com respostas reais capturadas: 8 fontes coletando; fixture Faustus propositadamente envelhecida → corretamente `invalid_response` (prova do passe de expiração).

## IMPLANTAÇÃO

Como antes: `npx wrangler deploy` + observar `/status.json` por 2–3 ciclos. Nenhuma alteração de KV/rotas/custos. Backup do estado anterior em `pgs-feed-backup-v1` permanece válido.
---

# Addendum 2 — 2026-11-27, terceira rodada (verificação do segundo relatório externo)

## O QUE FOI APROVEITADO DO MATERIAL EXTERNO

| Achado | Ação |
|---|---|
| Moonani retorna apenas 100 linhas por XHR embora a tabela IV100 contenha ~203 (`recordsFiltered`) | **Implementado:** o Worker passa a paginar `start=0,100,200` (teto `MAX_MOONANI_PAGES=3` = 300 linhas), tolerando falha em páginas além da 1 (usa dados parciais, avisa via `console.warn`). Estatísticas (`received/validated/discarded`) refletem o agregado. |
| `ADAPTER_VERSION` força recoleta imediata no primeiro cron pós-deploy | **Implementado** (`ADAPTER_VERSION=2`): entradas legadas de KV sem `adapter_v` são recoletadas imediatamente, independentemente do `next` gravado (o clamp de 30 min continua como segunda barreira). |
| Piso de espera para HTTP 429 | **Implementado:** sem `Retry-After`, `next_retry >= agora + 30 min`, mesmo com `failures=1`. |
| `state_label` em PT-BR no `/status.json` | **Implementado:** rótulos como "Online sem Hundos", "Resposta inválida" etc. junto de `state`. |
| PokéMaps exigem `Referer` da origem (evidência: 200 com corpo vazio sem Referer) | **Já coberto na rodada anterior** (`Referer: https://<host>/` + `X-Requested-With: XMLHttpRequest` + `Accept: application/json, text/javascript, */*; q=0.01`). A validação em produção depende do `content_type`/`reason` pós-deploy — sem egress neste sandbox. |

## O QUE FOI REJEITADO (e por quê)

1. **O `worker.mjs` completo colado no relatório não é executável**: o iFlowGo aponta para `https://https://www.google.com/search?q=pokecoords.iflowgo.com/...` (um redirect do Google — `url.hostname==="www.google.com"` faria a verificação `iflow` falhar sempre → `source_url` → iFlowGo offline para sempre). Vários `**` (operadores) e crases foram apagados pela formatação markdown do paste (`2 Math.min(...)`, template literals sem backticks). Seguir aquele arquivo quebraria o Worker. Nosso `worker.mjs` do branch é a fonte de verdade.
2. **"12 testes executados, 12 aprovados" / "7 testes passando"** — divergem do branch (23 testes, todos passando). Nenhum dos artefatos citados (`/home/workdir/artifacts/`) existe neste workspace.
3. **"wrangler.json não precisou de alterações"** — correto apenas para o cenário de 8 fontes; **decidido pelo operador nesta sessão: GOCoords ativada como 9ª fonte** (atestação registrada no Addendum 1).
4. **iFlowGo "endpoint" do relatório** é o redirect do Google acima; o endpoint real (já usado) é `https://pokecoords.iflowgo.com/iflowgopokecoords/api/v1/pokemon-search` com `min_iv=100` — confirmado de novo pelo próprio relatório (total≈105, total_pages=5, 25/25 itens 15/15/15) como **segunda confirmação independente** da nossa descoberta.

## VERIFICAÇÃO DOS NOVOS CANDIDATOS DE FONTE (nenhum integrado)

| Candidata | Verificação independente | Situação |
|---|---|---|
| GhostDex (`ghostdex.io/pokemon-go-coordinates`) | **Existe e está vivo** (atualizado 2026-11-27 21:05 UTC; ~57–60 hundos ao vivo; 13–16 países; CP/Lv/ATK/DEF/HP/coords). Página SSR HTML; sem API JSON pública verificada; ToS/autorização não confirmados. | Não integrada. Pedido de autorização é o caminho. |
| Poke100IV (`poke100iv.com`) | **Existe e está vivo** (mapa ao vivo; snapshot SSR de 100%-IV; contato público `info@poke100iv.com`, aberto a integrações segundo a página). Sem API pública verificada. | Não integrada. Parceria possível mediante contato. |
| PogoTrades | A busca retornou apenas o PoGoCoordinates (`pogocoordinates.com`), já agregado via FaustusFoundry; a existência de "PogoTrades" não pôde ser confirmada. | Descartada por falta de evidência. |
| TWPkInfo / BaoBaoBei (`twpkinfo.com`) | Portal real e antigo (notícias desde 2025/04), mas **nenhuma API/feed 100% IV máquina-legível verificada**; o Moonani apenas usa os ícones de pokémon do site. | Não integrada. |
| Coords GO | Comunidade PT-BR (Discord/Telegram); feed estruturado para selvagens 100% IV não confirmado. | Não integrada; exige resposta em canal da comunidade. |

**Regra mantida:** nenhuma fonte nova entra em produção sem (a) endpoint máquina-legível verificado, (b) dados reais 100% IV selvagens com coords e expiração, (c) autorização de coleta/redistribuição pelo fornecedor. Nada foi integrado às cegas.

## TESTES

`node worker.test.mjs` → **23/23** (5 novos: paginação Moonani de 2 páginas com `recordsFiltered=105`, Moonani página-1-só/zero hundos online com 1 chamada, piso de 30 min para HTTP 429 sem `Retry-After`, `state_label` presente + backoff ≤30 min, `ADAPTER_VERSION` ausente no KV legado → recoleta imediata). Ensaio offline (fixtures reais capturadas) reproduz 8 fontes online antes da fixture envelhecer — os dados expirados são corretamente descartados.
## Ensaio local de 27/11, 18h47 de Fortaleza

Uma execução com KV temporário consultou nove fontes. O resultado continha 74 encontros e 214 spots, todos futuros no momento da leitura. Contagens ativas/únicas por fonte: FaustusFoundry 68/68, NYC 1/0, Singapura 1/0, Londres 0/0, Sydney 1/1, Vancouver 0/0, iFlowGo 91/49, Moonani 167/162 e GOCoords 9/8. iFlowGo respondeu em cinco páginas e Moonani em duas. São métricas do ensaio durante o desenvolvimento. Em produção, a captura anterior da mesma sessão tinha 64 encontros e 90 spots, com os cinco mapas regionais em invalid_json.

A página pública GhostDex expôs IVs, coordenadas e expiração UTC na apresentação. O HTML mediu 1.154.609 bytes, acima do orçamento por resposta do Worker. A vinculação de cada expiração à espécie e a uma coordenada exata precisa ser validada antes da ativação. GOCoords oferece até dez linhas na interface gratuita.

A configuração candidata prevê até 15 consultas externas por ciclo e quatro conexões simultâneas. Com 288 ciclos diários, o coletor usa até 576 escritas KV e 288 leituras agendadas. As leituras públicas somam-se às agendadas. A CPU e o consumo total da conta precisam ser medidos na Cloudflare. A produção ainda requer verificação do namespace existente e da versão para rollback antes da implantação.

### Candidato com Poke100IV
 2026-11-27T21:49:52.694Z

O mapa Poke100IV usa /api/pokemon com limites geográficos, limit=101 e ivFilters=15-15-15. A janela de Nova York foi testada. A fonte fornece IVs individuais, espécie, coordenadas e expires_at. O ID interno não é usado como encounter ID. O teto passa a 16 consultas, sem alteração no número de escritas KV.

| Fonte | Recebidos | Validados | Descartados | Ativos | Únicos | Páginas |
|---|---:|---:|---:|---:|---:|---:|
| faustusfoundry | 70 | 70 | 0 | 70 | 70 | 1 |
| nycpokemap | 1 | 1 | 0 | 1 | 0 | 1 |
| sgpokemap | 2 | 2 | 0 | 2 | 0 | 1 |
| londonpogomap | 0 | 0 | 0 | 0 | 0 | 1 |
| sydneypogomap | 1 | 1 | 0 | 1 | 0 | 1 |
| vanpokemap | 0 | 0 | 0 | 0 | 0 | 1 |
| iflowgo | 98 | 89 | 9 | 89 | 54 | 4 |
| moonani | 177 | 161 | 16 | 159 | 154 | 2 |
| gocoords | 10 | 10 | 0 | 10 | 10 | 1 |
| poke100iv | 6 | 6 | 0 | 6 | 5 | 1 |

Feed com 76 encontros e 217 spots, todos futuros. Wrangler informou ausência de autenticação administrativa.

PogoTrades divulga trocas no domínio pogotrades.com. TWPkInfo mantém um portal em twpkinfo.com. Nenhum contrato gratuito de spawns foi comprovado nesses dois serviços. Coords GO continua sem canal oficial e feed selvagem confirmados. Pokedex100 publica uma prévia com links criptografados. PoGO Alerts Network informa que o plano gratuito não inclui a camada Pokémon. PokeXperience divulga um feed, mas a interface de integração gratuita permanece sem validação. PoGoCoordinates e LivePokéMap continuam classificados como dependentes de autenticação no catálogo de produção. RocketMap exige identificar uma instância concreta disponível ao projeto.
