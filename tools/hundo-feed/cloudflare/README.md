# Feed de Hundos do PGS

O Worker publica o contrato v1 em `/hundos.json`. O agendamento UTC dispara a cada minuto. O Durable Object SQLite `FeedPublisher`, com nome fixo, serializa as coletas e persiste a última publicação. Um alarme do mesmo objeto mantém a cadência durante a propagação de mudanças do cron. Os dois compartilham a mesma trava e a mesma verificação de minuto. O KV `FEED` fornece o estado anterior na migração e recebe checkpoints em minutos múltiplos de 15. As leituras públicas têm cache de 15 segundos. A filtragem exige ao menos 60 segundos restantes ao montar a resposta.

## Fontes

| Fonte | Intervalo de consulta |
|---|---:|
| Faustus Foundry | 60 s |
| NYC, Singapore, London, Sydney, Vancouver | 600 s por cidade |
| iFlowGo | 600 s |
| Moonani | 900 s |
| GoCoords | 300 s |
| Poke100IV | 600 s |
| PoGoCoordinates direto | 180 s quando POGO_TOKEN está configurado |

Cada fonte tem prazo de 12 segundos. Até quatro fontes são consultadas em paralelo. Falhas preservam registros válidos e aplicam backoff, inclusive o prazo de Retry-After. O estado individual está em `/status.json`, incluindo última tentativa, último sucesso, contagens e status HTTP. O catálogo está em `/sources.json`. O timestamp `fetched_ms` corresponde à coleta bem-sucedida mais recente. Um cron executado sem nenhuma coleta bem-sucedida não torna os dados mais recentes.

O adaptador direto usa um token próprio em Cloudflare Secrets, no campo `POGO_TOKEN`. Consulta uma das oito regiões por rodada e revela no máximo um encontro ainda desconhecido. Somente o retorno de reveal fornece coordenadas para publicação. Resultados do mapa com coordenadas aproximadas são descartados. A integração requer uma conta autorizada para consulta e revelação. A amostragem e os limites dos provedores impedem cobertura integral.

Os mapas usam atributos individuais quando fornecidos. O feed compacto de Faustus atesta os IVs e a precisão por contrato e não expõe os atributos individuais para reverificação. A lista de Hundos tem IDs de encontro e a de spots tem identificadores locais. O cliente lê ambas. Na versão 0.0.5 a espera normal entre consultas é de cinco minutos, com antecipação para um minuto após falha ou fila baixa. A confirmação de shiny ocorre no jogo.

## Testes e publicação

Execute neste diretório com Node.js e Wrangler 4 autenticado na conta do Worker. O arquivo wrangler.json referencia o KV de produção e define o Durable Object, a migração SQLite, o limitador público e o cron.

```sh
node --test worker.test.mjs
npx wrangler@4 deploy --dry-run
npx wrangler@4 deploy --keep-vars
```

Verifique o histórico de tempos em /status.json e os dados em /hundos.json por vários minutos. Observe a expiração, as mudanças de registros e os limites individuais de cada origem. A cada dia são previstos 1.440 disparos e até 192 gravações de checkpoint no KV. Leituras públicas e operações do Durable Object também contam para as quotas do plano.

## Recuperação da versão anterior

A versão anterior ad96424c-b507-4c26-808b-7955d86bea49 foi publicada a partir de 7776bc2. Seu cron era */5 * * * *. O operador tem uma exportação do módulo implantado, configurações, agendamentos e histórico anterior. A migração adicionou um namespace SQLite. Para recuperar o comportamento anterior preservando esse estado, prepare uma nova versão a partir do coletor de 7776bc2, mantenha a classe exportada FeedPublisher e o binding já migrado, restaure o SOURCES do backup e o cron anterior, teste e publique. O coletor anterior lê os checkpoints do mesmo KV. Verifique a primeira coleta antes de encerrar a recuperação. Esse procedimento de retorno não foi executado em produção.
