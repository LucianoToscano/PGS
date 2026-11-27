# PGS: revisão e integração da comunidade

Revisão de **27/11/2026**, sobre PGRazor `1106592aa045759f55f594ff6968f783ff636fe9` (v0.3.8), compatível com o perfil Pokémon GO **0.439.0 / 2026111602**. As mudanças desta rodada formam uma candidata PGS; não constituem uma nova versão oficial do PGRazor.

## Cobertura

Foram consultadas as coleções de [issues](https://github.com/jpitty03/PGRazor/issues), [PRs](https://github.com/jpitty03/PGRazor/pulls) e [forks](https://github.com/jpitty03/PGRazor/forks):

| Inventário | Quantidade |
| --- | ---: |
| Issues reais | 13: 10 abertas e 3 fechadas |
| PRs | 9: 4 abertos, 4 incorporados e 1 fechado sem merge |
| Entradas na coleção de forks | 29 |
| Forks acessíveis | 27 |
| Entradas indisponíveis, com resposta 404 | 2 |
| Branches acessíveis enumeradas | 78 |
| Pontas distintas de histórico | 43 |
| Pontas ancestrais da base | 21 |
| Pontas divergentes | 22 |

A coleção de issues continha 22 objetos porque também inclui os nove PRs. A segunda página de forks estava vazia. As 78 branches foram comparadas por histórico; a revisão detalhada de código concentrou-se nas mudanças candidatas. Isso não equivale a uma auditoria linha a linha de todos os forks. O [inventário de branches](PGS_FORK_INVENTORY.json) preserva os nomes, commits e diferenças encontrados.

## O que foi integrado

| Alteração | Origem | Adaptação e proteção adicional |
| --- | --- | --- |
| IVs reais em capturas VGP+ | [PR 18](https://github.com/jpitty03/PGRazor/pull/18), Fixuuu, `02a6c2a388b4a96078a7f4390df63d7742e0e646`; [issue 9](https://github.com/jpitty03/PGRazor/issues/9) | Lê a cadeia do encontro, valida cada classe e mantém os objetos sob GC. Fixtures distinguem 41/45 e 40/45 também pela bola escolhida. |
| Camada visual dos IVs | Trecho isolado do [PR 12](https://github.com/jpitty03/PGRazor/pull/12), Hugo Alves/Pokematrix; [issue 7](https://github.com/jpitty03/PGRazor/issues/7) | Atualiza a ordem do Canvas a cada exibição, consultando o pai para não aumentar indefinidamente sua própria ordem. |
| Atualização após power-up | Implementação PGS da [issue 8](https://github.com/jpitty03/PGRazor/issues/8) | Usa os campos já validados e o tick Unity existente. Limite de oito painéis, um refresh por tick e intervalo de 150 ms. Trata troca de proto/Text, GC, destruição e revogação; não importa TM shortcuts ou scanners do PR 12. |
| Trava direcional do joystick | [PR 10](https://github.com/jpitty03/PGRazor/pull/10), 7sarus | Preserva dimensões originais; cancelar/ocultar usa `stopManualMotion()` para não apagar uma rota independente. Mudança ou perda de câmera exige novo gesto. |
| Intervalo LivePokeMap e backup Global | [PR 17](https://github.com/jpitty03/PGRazor/pull/17), Fixuuu, `76fc5eaa4f1776b899fae88f27b48ebcfc75b392` | Corrige o piso aplicado antes do jitter no PR. Relógio monotônico, uma requisição por vez, backoff preservado e reagendamento na importação. Resultados antigos não entram em outra geração. |
| Localização real para VGP | Implementação PGS da [issue 3](https://github.com/jpitty03/PGRazor/issues/3) | Observa o callback do provider atual quando spoofing está desligado. Publica latitude/longitude válidas juntas e conserva o callback original. A parte do relato sobre auto-battle não foi reproduzida. |
| Atalho de presentes | Implementação PGS da [issue 19](https://github.com/jpitty03/PGRazor/issues/19) | Abre o diálogo existente sem iniciar envio. Bit 8192, máscara 16383, mantendo os bits antigos e a compatibilidade dos backups. |
| Recuperação de alimentação do buddy | [Commit 0d1b600](https://github.com/Fixuuu/PGRazor/commit/0d1b600a22d4cd1e9183b4cd78b2ca1f8ff90afa), branch `feature/device-regression` conservada nos forks | Após resposta perdida, só libera a espera quando o mesmo buddy é observado alimentado; não repete o pedido nem registra sucesso presumido. Acrescentada proteção para relógio inválido. |
| Silver Pinap e preferências antigas | Correção PGS identificada na revisão do PR 12 e da base | Escolhas novas usam 708. Preferências antigas 707 são migradas ao carregar, com prioridade preservada e validação de duplicatas. O estoque real 707 continua separado; o nome histórico do arquivo de ícone é preservado. |
| Ferramentas de build no Linux | [Commit f3a15385](https://github.com/DevPGSV/PGRazor/commit/f3a15385d3bd7fbbfa74bdb705d41a0e7c30ec50), DevPGSV | Seleciona executáveis do SDK conforme o sistema e corrige caminhos dos testes. Mantém as ferramentas e os nomes Windows. Não importa configuração Docker ou assinatura de outro fork. |

O arquivo `LICENSE` MIT e os avisos de terceiros permanecem preservados. Os autores das contribuições acima são identificados pelas fontes; ajustes de integração e fixtures adicionais pertencem à manutenção deste fork.

## Destino de todos os PRs

| PR | Decisão |
| --- | --- |
| [1](https://github.com/jpitty03/PGRazor/pull/1), [5](https://github.com/jpitty03/PGRazor/pull/5), [6](https://github.com/jpitty03/PGRazor/pull/6), [11](https://github.com/jpitty03/PGRazor/pull/11) | Já incorporados à base: overlays, CMake/Windows, interface/busca e ART/Vector. Não reaplicados. |
| [10](https://github.com/jpitty03/PGRazor/pull/10), [17](https://github.com/jpitty03/PGRazor/pull/17), [18](https://github.com/jpitty03/PGRazor/pull/18) | Integrados com as correções descritas acima. |
| [12](https://github.com/jpitty03/PGRazor/pull/12) | Revisado o head `31c6f2b3`. Somente a camada IV foi portada; o refresh foi implementado separadamente. O pacote de 70 arquivos continua exigindo revisão própria. O grupo de regras por tags repete a confusão Silver Pinap 707/708; a condição `iv_valid` exige soma maior que zero antes de verificar nundo, impedindo a correspondência de 0/0/0. Os testes de berries desse grupo não exercitam a política nativa. Não importar integralmente. |
| [2](https://github.com/jpitty03/PGRazor/pull/2) | Fechado sem merge; pacote antigo e amplo, com funções depois reimplementadas upstream. A revisão registra problemas de proteção de inventário, migração e thread Unity. Não reaplicado. |

## Destino de todas as issues

| Issue | Situação desta rodada |
| --- | --- |
| [3](https://github.com/jpitty03/PGRazor/issues/3) | Corrigido o caminho de localização real para VGP; auto-battle permanece sem reprodução. |
| [4](https://github.com/jpitty03/PGRazor/issues/4) | Fechada; o limiar global 0–100 já existe. Limiares diferentes por espécie seriam uma função nova. |
| [7](https://github.com/jpitty03/PGRazor/issues/7), [8](https://github.com/jpitty03/PGRazor/issues/8), [9](https://github.com/jpitty03/PGRazor/issues/9) | Correções de camada, refresh e origem dos IVs integradas. Falta observação no aparelho. |
| [13](https://github.com/jpitty03/PGRazor/issues/13) | Exportação CSV/JSON/PvPoke é uma função nova; há código em um fork, mas depende de portar a coleta de inventário e o fluxo de exportação. |
| [14](https://github.com/jpitty03/PGRazor/issues/14) | Exclusão de cartões-postais exige seleção e proteção explícitas; não foi acrescentada exclusão automática. |
| [15](https://github.com/jpitty03/PGRazor/issues/15) | Fechada sem reprodução técnica conclusiva. O ajuste de pacing não é apresentado como prova de resolver esse relato. |
| [16](https://github.com/jpitty03/PGRazor/issues/16) | Escolha de ataque carregado requer política de energia, efetividade e estado da batalha. Não existe patch pequeno validado nesse issue. |
| [19](https://github.com/jpitty03/PGRazor/issues/19) | Atalho integrado, com persistência e backup. |
| [20](https://github.com/jpitty03/PGRazor/issues/20) | Listas e alcance ampliado são funções novas. O scanner atual usa o que o jogo carregou; aumentar um número não garante novos alvos. |
| [21](https://github.com/jpitty03/PGRazor/issues/21) | A exibição `ivOwned` já existe. As correções 7/8 a complementam; Keep All tem outra finalidade. |
| [22](https://github.com/jpitty03/PGRazor/issues/22) | Fechada pelo autor após confirmar a versão nova; controle de transferência e proteções já existem. |

## Outros grupos de forks

| Grupo | Decisão |
| --- | --- |
| DevPGSV `feature/linux-build` | Portabilidade mínima integrada. Docker/limpeza/assinatura adicionais fixam jogo 0.437.0 e não são necessários ao build 0.439.0. |
| DevPGSV `feature/http-api` | 139 arquivos: servidor local, credenciais e exportação. Requer integração própria dos contratos e da superfície de acesso. |
| `feature/device-regression`, repetida em vários forks | Buddy isolado; executor/diagnósticos restantes precisam de portabilidade e um dispositivo real. |
| `feature/shiny-scanner` | Branch antiga usa JavaScript. O scanner atual é compilado; não reintroduzir o runtime antigo. |
| `feature/showcase-keepers` | Metadados do jogo 0.435.2; proteção/ranking requer portabilidade para 0.439.0. |
| `research-deep-radar` | Protótipo explicitamente de pesquisa, não um recurso pronto. |
| 7sarus `feature/joystick-lock` | Preferido o PR 10 isolado; a branch anterior acumula outras mudanças. |
| 7sarus `feature/overlay-hide` | O próprio fork reverteu parte do gesto; também desativa packaging nonroot. Não importar integralmente. |
| 7sarus `feature/pokemon-dump` | Coleta/exportação precisa de integração independente; herda outras mudanças de seu main. |
| 7sarus `main` | Remove x86_64 e desfaz o updater, entre outras alterações. Não substituir o PGS por esse main. |
| belalsalah74 Auto-Max | Coordenador de sessão; descoberta, entrada, gastos e captura continuam manuais. Falta suíte de comportamento do controlador. |
| Petit-Prince-dev | Grande redesign francês/root; remove multicontas, rotas e pesquisa. Não importar o conjunto. |
| dojistarman/PGRazor-Savant | Identidade root e contexto PvP próprios; observação em outro aparelho não valida o PGS atual. |
| randrew87/PGRazorX | Pacote antigo do PR 2, com sobreposição a funções já incorporadas. |
| ar5hil/Rasiel | Alpha antiga; necessidade de portabilidade já coberta pelo patch mais atual. |
| Benjaminlooi ART/Vector | Já incorporado por squash no PR 11; os arquivos relevantes são iguais à base. |
| sreenushenoy07/PGRazor-Rooted e sreenushenoy/PGRazor-root | Resposta 404; não foi possível revisar o conteúdo. |

Quinze forks não acrescentavam commits fora do histórico já incorporado: ReneeAraujo, celestialeye, JxstMichie, vantrox, Axe2230, arisuryohei911-dot, kunal2801, dhanush-c-c, gloiae, gv2598, foxartic, privacyportalUK, Archit-barge, NPSummers e Slumpz2460. As branches padrão de outros forks também podem estar atrasadas, mesmo quando uma branch de recurso contém mudanças.

## Verificação e limites

As regressões executam classes Java e módulos C++ de produção. Há controles negativos que falham com o código anterior para camada/refresh IV, Buddy e Silver Pinap. O job Linux de CI descobre os fixtures nativos; os demais checks e a compilação Android permanecem no job Windows.

Comandos de referência:

```bash
python -B tools/check.py
python -B pgs/build.py
python -B pgs/rooted_installer.py --check
python -B -m unittest discover -s pgs/test -p 'test_*_native.py' -v
python -B pgs/native_build.py --abi arm64-v8a
python -B tools/source_bundle.py
```

Fixtures simulam chamadas do jogo, Canvas, hooks e relógio onde necessário. Não comprovam renderização Unity, trampolins no aparelho, instalação, login, resposta do servidor ou ausência de punições. Nenhum teste automatizado desta revisão captura/transfere Pokémon reais, alimenta buddy real ou envia presentes. O artefato mantém `device_tested: false` até existir observação correspondente.

Os pacotes amplos e pedidos novos registrados acima permanecem como trabalho identificado, e não como funcionalidades concluídas. Foram preservadas as razões técnicas para que uma futura integração possa começar do ponto certo.
