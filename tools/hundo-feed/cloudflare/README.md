# PGS Hundo Feed

## Português

O Worker lê feeds compactos v1 autorizados. Use Workers Free, a pasta `tools/hundo-feed/cloudflare` e o comando `npx wrangler deploy`. O Wrangler provisiona o vínculo KV `FEED`. Configure `SOURCES` como variável JSON com uma lista de objetos. Cada objeto precisa de `name` (identificador curto), `url` (HTTPS terminado em /hundos.json) e `interval_s` (inteiro, mínimo 300). Use apenas fontes com permissão para coleta e redistribuição. A lista vazia não faz requisições externas. Não inclua tokens em URLs. O coletor Python permanece disponível no diretório pai.

O cron a cada cinco minutos grava no máximo 288 instantâneos diários em operação normal. Falhas preservam os dados anteriores e aumentam o intervalo entre tentativas. Consulte /hundos.json para verificar o horário da última coleta bem-sucedida, contagens e estado de cada fonte. Antes da primeira coleta bem-sucedida, o serviço responde HTTP 503. Valide várias atualizações, compatibilidade no dispositivo e expiração antes de alterar o APK. Para recuperar a versão anterior do código, use o histórico de implantações do Worker. Uma reversão de código não restaura dados do KV.

## English

Use Workers Free with the project root `tools/hundo-feed/cloudflare` and deploy command `npx wrangler deploy`. Wrangler provisions the dedicated `FEED` KV binding. Set `SOURCES` to a JSON array of authorized v1 feeds. Each entry requires a short `name`, an HTTPS `url` ending in /hundos.json, and integer `interval_s` of at least 300 seconds. Confirm automated collection and public redistribution rights first. An empty list performs no upstream requests. Keep credentials out of URLs. The original Python service is available in the parent directory.

A five-minute cron writes up to 288 snapshots per day in normal operation. Failures retain prior rows and extend the retry interval. Inspect /hundos.json for the last successful source timestamp, source counts and status. Before the first successful poll the endpoint returns HTTP 503. Verify successive updates, expiry and on-device compatibility before changing the APK. Use Worker deployment history for code rollback. Rolling back code does not restore KV data.
