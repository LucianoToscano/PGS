# PGS — migração dos nomes internos: Etapa 1

**Estado atual (etapa 15):** a etapa 12 já migrou Java/JNI, nomes das bibliotecas nativas e layout dos assets nas fontes. As seções anteriores são registros históricos, não o layout atual de compilação. Ainda não foram verificados um APK completo assinado e a atualização em dispositivo físico.

Estado: migração do código iniciada na branch `refactor/pgs-native-build-names-phase1`. Esta etapa **não** publica um novo APK assinado.

[🇺🇸 English](../en/PGS_TECHNICAL_MIGRATION.md) · [🇧🇷 Português (Brasil)](PGS_TECHNICAL_MIGRATION.md)

## O que está sendo renomeado

- Arquivos principais: `pgs_native.cpp` → `pgs_native.cpp`; `pgs.map` → `pgs.map`.
- Cabeçalhos: `pgs_internal.h` → `pgs_internal.h`; `pgs_native_api.h` → `pgs_native_api.h`, com arquivo de encaminhamento para includes antigos.
- Script de exportação ART: `pgs-art.map` → `pgs-art.map`.
- Alvos internos do CMake: `pgs_core` → `pgs_core` e `pgs_art` → `pgs_art`.
- Novas variáveis `PGS_NATIVE_PILOT`, `PGS_NATIVE_DOWNLOAD`, `PGS_ART_NDK` e `PGS_NATIVE_DEPS`, mantendo os aliases anteriores.
- Novo comando de Windows `pgs.cmd`; o antigo `nonroot.cmd` continua funcionando como encaminhamento.

## Compatibilidade obrigatória

Os binários `libpgs-core.so` e `libpgs-art.so`, a função nativa exportada `pgs_native_api`, o namespace Java `dev.pgs` e os caminhos `assets/pgs` continuam temporariamente iguais, pois são referenciados pelo carregamento do aplicativo. A troca integral deles exige atualizar os consumidores ao mesmo tempo e criar testes de compatibilidade.

**Nada altera** o nome instalado **Pokémon GO**, o package **`com.nianticlabs.pokemongo`**, o certificado PGS, o `versionCode` ou os dados de instalações anteriores.

A etapa será verificada com testes de código e compilação. Não considerar que houve teste físico ou geração de APK completo nesta PR.

## Próximas etapas

Migrar gradualmente classes Java/JNI, binários, arquivos de execução e preferências salvas, com aliases, testes e preservação de dados. A autenticação Google precisa de credenciais OAuth próprias autorizadas, sem inventar IDs. Somente após compilação completa e teste de atualização sobre o APK instalado será possível lançar uma versão.

Acompanhe o restante na [issue #38](https://github.com/LucianoToscano/PGS/issues/38). O histórico e os créditos de licença permanecem preservados.

## Etapa 2 — migração dos includes C++

Os módulos C++ do projeto e os testes nativos passam a incluir `pgs_native_api.h`, no lugar de `pgs_native_api.h`. O cabeçalho de compatibilidade antigo continua disponível para builds anteriores. Uma nova verificação automática impede que includes antigos retornem ao código.

Esta etapa não altera os símbolos exportados, os nomes de bibliotecas `.so`, o identificador Android, o certificado ou as preferências salvas. Aprovação dos testes de código **não** significa APK completo recompilado ou atualização física aprovada.

## Etapa 3 — fábrica nativa PGS sem perder compatibilidade

- A nova função C exportada `pgs_native_api(uint32_t)` é o nome principal. A função antiga `pgs_native_api(uint32_t)` continua presente e encaminha à nova. As duas devolvem **as mesmas tabelas imutáveis v1/v2** para as versões válidas e `null` para versões incompatíveis.
- O script `pgs.map`, a verificação de símbolos ELF e o teste nativo exigem exatamente **três símbolos** exportados: `JNI_OnLoad`, `pgs_native_api` e `pgs_native_api`. Os demais ficam ocultos.
- Constantes, códigos de erro e tipos de funções podem ser escritos como `PGS_*` / `pgs_*`. Os nomes antigos funcionam como aliases e o tamanho e a ordem dos campos das tabelas v1/v2 não mudam.
- O Android ainda carrega `libpgs-core.so` e `libpgs-art.so`, e os módulos Java/JNI podem continuar usando o nome antigo. Não são alterados o pacote Java `dev.pgs`, backups, dados, pacote Android `com.nianticlabs.pokemongo`, chave PGS ou `versionCode`.
- Esta etapa depende de testes de código e símbolos nativos. **Não** é uma compilação de APK completo nem comprova atualização física. O restante permanece na [issue #38](https://github.com/LucianoToscano/PGS/issues/38).

## Etapa 4 — nomes PGS no motor de hooks C++

- As implementações internas principais passam a ser `pgs_hook`, `pgs_unhook`, `pgs_instrument` e `pgs_hook_diag`. Os nomes antigos `pgs_*` continuam funcionando como encaminhamento, usando **o mesmo mutex e registro Dobby**.
- Os tipos `PgsHookDiag` e `PgsPaddingRanges` conservam o layout e os cálculos originais. O núcleo chama os nomes PGS e o teste de ilhas ARM valida ambas as interfaces.
- Os logs de erro do Android passam a usar a etiqueta `PGS`. Esta etapa não exporta novos símbolos ELF, não muda arquivos `.so`, package, certificado, assinatura, nem cria hooks adicionais ou APK completo.
- A migração de Java/JNI, bibliotecas, caminhos e preferências exige verificação de instalação física e continua na [issue #38](https://github.com/LucianoToscano/PGS/issues/38).

## Etapa 5 — opções não confidenciais de compilação com nomes PGS

O compilador Java em `pgs/build.py` agora usa prioritariamente `PGS_VERSION`, `PGS_BUILD_TOOLS` e `PGS_ANDROID_PLATFORM`. Os aliases `PGS_*` continuam aceitos para manter os workflows existentes e as compilações antigas. Se ambas as opções estiverem definidas, a versão PGS não vazia prevalece; valores vazios utilizam o alias.

As variáveis de chave e senhas `PGS_KEYSTORE`, o arquivo da chave, os caminhos de preview/DEX, o pacote Android, o certificado definitivo e o registro de `versionCode` **não mudam** nesta etapa. A alteração não gera outra chave. Um teste isolado verifica padrões, aliases, precedência e versão sem executar assinatura ou Android SDK. Testes de fonte aprovados não comprovam APK completo nem instalação no celular.

## Etapa 6 — consumidores diretos de hooks (alimentação de companheiro e itens)

Os módulos de produção `buddy_feeding.cpp` e `items.cpp` passam a chamar diretamente `pgs_hook` (dois e cinco pontos de chamada, respectivamente). Os respectivos simuladores isolados para Linux definem o símbolo principal correspondente; os testes existentes de compilação e execução verificam os consumidores migrados sem depender do encaminhamento antigo. O teste de identidade também impede o retorno acidental de `pgs_hook` nesses pontos.

A mudança é apenas de nomenclatura: argumentos, ordem de instalação, encadeamento original, estado, motor Dobby, ABI C, SONAME, JNI, pacote, assinatura, preferências e registro de versões permanecem iguais. Os encaminhamentos legados do motor continuam disponíveis para os outros consumidores; as declarações fracas e resoluções dinâmicas de `interaction_host.cpp` e `camera_host.cpp` ficam para uma etapa separada. A integração depende da aprovação das verificações de código e regressões nativas Linux. Os simuladores não comprovam funcionamento em aparelho físico ou instalação do APK; esta etapa não gera APK completo. Consulte a [issue #38](https://github.com/LucianoToscano/PGS/issues/38).

## Etapa 7 — consumidores diretos de hooks (exibição de IV e inventário)

As chamadas diretas existentes em `iv_display.cpp` (dois pontos) e `inventory_host.cpp` (um ponto) passam a usar `pgs_hook`. Os simuladores vinculados (`iv_owned_refresh_test.cpp`, `inventory_berries_policy_test.cpp` e o adaptador de registro gerado em `test_iv_owned_refresh_native.py`) fornecem o nome principal correspondente. Os testes existentes de compilação e execução Linux são preservados, com uma verificação adicional de identidade para evitar o retorno da grafia antiga nesses consumidores e simuladores.

A mudança é somente de nomenclatura. Alvos, argumentos, ordem, estado, registro Dobby, ABI, JNI, SONAME, identidade Android, assinatura e dados persistidos permanecem iguais. O simulador de política de inventário não instala hooks sociais, e os testes Linux não comprovam a modificação de instruções em Android real. Os encaminhamentos antigos e consumidores com resolução fraca/dinâmica continuam intactos. A integração exige verificações de código e regressões Linux aprovadas. Nenhum APK novo é gerado ou publicado. O restante é acompanhado na [issue #38](https://github.com/LucianoToscano/PGS/issues/38).

## Etapa 8 — nome público do pacote de código e ferramentas

O pacote de código-fonte gerado por `python -B tools/source_bundle.py` passa a ser `dist/PGS-source-tools.zip`, e o workflow Source checks o publica como `PGS-source-tools`. A seleção de arquivos, o conteúdo, as verificações de segurança, a lista permitida de arquivos locais, as permissões de CI e o prazo de retenção permanecem iguais. Dois testes de regressão verificam o nome e o conteúdo do ZIP em um repositório Git temporário e a configuração de upload correspondente no workflow.

O novo nome vale para empacotamentos futuros; artefatos históricos e arquivos locais já baixados não são renomeados nem removidos. Scripts externos que utilizem o nome anterior precisam atualizar as referências. O ZIP contém código e ferramentas, não um APK instalável. Esta etapa não altera release, assinatura, identidade Android, dados persistidos ou ABI de execução. O restante da migração é acompanhado na [issue #38](https://github.com/LucianoToscano/PGS/issues/38).

## Etapa 9 — migração de identidade em lote

Um único lote revisável atualiza 34 fontes nativas de produção e 12 simuladores/adaptadores de teste para chamar ou definir os símbolos principais PGS do motor de hooks (`pgs_hook`, `pgs_unhook`, `pgs_instrument`). Os encaminhamentos antigos e o teste de compatibilidade do motor permanecem intactos. Os consumidores de resolução fraca/dinâmica (`interaction_host.cpp`, `camera_host.cpp`, `runtime_host.cpp`) e seus simuladores ficam fora deste lote. A mudança é somente de grafia; não introduz novos hooks, altera alvos, argumentos, ordem, layout de dados ou comportamento.

Cinco workflows passam a usar as opções não confidenciais `PGS_BUILD_TOOLS`, `PGS_ANDROID_PLATFORM` e `PGS_VERSION`. Os leitores dos testes de SDK aceitam primeiro os nomes PGS e depois os aliases antigos, conservando os padrões. Referências e valores de segredos, assinatura, registro de versões, APK, namespace Java/JNI, nomes de bibliotecas instaladas, dados persistidos, licenças e pasta do projeto permanecem iguais. Duas verificações adicionais protegem o lote e os nomes dos workflows. As verificações de código e regressões Linux são obrigatórias antes da integração; não equivalem a compilação Android assinada nem instalação física. Uma branch de backup temporária preserva o ponto anterior à migração em lote. O restante está na [issue #38](https://github.com/LucianoToscano/PGS/issues/38).

## Etapa 10 — diretório do projeto no repositório

A pasta rastreada do projeto passa para pgs/. Caminhos de fontes, compilação, geradores, testes, documentação e CI são atualizados em conjunto. Nomes Java/JNI instalados, assets e caminhos de módulos, símbolos/SONAMEs, preferências, assinatura, release e registro de versão não são renomeados nesta etapa de organização do checkout. Arquivos locais de build/input não são movidos ou apagados pelo Git e permanecem ignorados no caminho anterior; mova apenas os próprios insumos locais revisados quando necessário. A compilação histórica da candidata v0.0.2 passa a ser manual para não regenerar a mesma versão assinada a cada manutenção. Verificações de código não comprovam atualização física.

## Etapa 11 — constantes e aliases de tipos nativos em lote

Um único lote atualiza 98 arquivos nativos de implementação/teste e cinco cabeçalhos de declaração: 438 usos de identificadores passam para 55 nomes PGS (33 constantes numéricas e 22 nomes de tipos typedef). Cinquenta e dois aliases são introduzidos e três aliases de tipos já existentes são reutilizados. Os valores numéricos originais, definições de tipos, tags de estruturas, tipos binários, layout dos campos e nomes exportados são preservados. Strings literais, cabeçalhos gerados, consumidores de diretivas do pré-processador e nomes configurados externamente ficam fora da substituição automática dos consumidores. O [inventário de aliases](../PGS_NATIVE_ALIAS_INVENTORY.json) registra cada correspondência exata. As verificações estáticas C++17 no Linux comparam todos os 55 valores ou identidades de tipos, além dos testes de fontes e regressões existentes.

O workflow temporário da migração não integra este commit. Package, assinatura, registro de versões, APK, namespace JNI, nomes das bibliotecas instaladas, dados persistidos e licenças não são alterados. A compilação em host e as verificações de código não comprovam o APK completo assinado nem a atualização física. O backup permanece disponível; o restante da migração está na [issue #38](https://github.com/LucianoToscano/PGS/issues/38).

## Etapa 12 — identidade de execução coordenada

As classes Java passam para `dev.pgs`, com atualização conjunta de bridges DEX gerados, manifests, simuladores Java, registros JNI e nomes de classes no carregador Root. Novas compilações usam `libpgs-core.so`, `libpgs-art.so`, `pgs.dex` e `assets/pgs/`. O alias da ABI, package instalado do jogo, IDs dos aplicativos Preview e Root, ID do módulo Root e marcador persistente Off continuam como contratos de compatibilidade. As verificações de entrada recusam pacotes já modificados nos dois layouts; os verificadores históricos reconhecem ambas as raízes de assets.

Os nomes lógicos PGS de arquivos e preferências passam por uma lista explícita que resolve os identificadores físicos existentes. Diretórios de contas, arquivos de recuperação AtomicFile, XML de preferências, formato dos backups e aliases do AndroidKeyStore não são renomeados, copiados, apagados ou redefinidos. Assim, preserva-se a compatibilidade dos dados existentes; não se trata de migração física no aparelho. A ferramenta histórica v0.0.2 que troca somente controles Java continua preservada, mas seus workflows históricos recusam o novo layout antes da compilação/assinatura, porque o APK completo antigo contém referências nativas/DEX incompatíveis. Qualquer release futuro exige reconstrução conjunta do runtime, assinatura permanente original, versionCode superior e validação de atualização em aparelho real.

O CI executa a bateria geral e acrescenta compilação Android sem assinatura das bibliotecas core e ART para arm64-v8a e x86_64, incluindo conferência de SONAME ELF. PRs e pushes à main disparam o CI regular; o job nativo Android roda em PRs ou manualmente. Não exige APK de jogo, chave de assinatura nem APK completo. Isso não comprova instalação física ou migração de contas. Contratos restantes: [issue #38](https://github.com/LucianoToscano/PGS/issues/38); atualização no aparelho: [issue #24](https://github.com/LucianoToscano/PGS/issues/24).

## Etapa 13 — autoria e caminhos restantes

As contribuições do PGS passam a ter aviso próprio de copyright sob MIT, junto ao aviso original preservado. O índice de licenças mantém as exclusões de terceiros e de imagens. O cabeçalho de encaminhamento legado sem uso interno passou para `pgs_native_api_compat.h`; clientes de código externo que usavam o include antigo devem atualizar para `pgs_native_api.h` (ou o novo cabeçalho). Ambas as funções de fábrica exportadas, aliases de tipos, tags de estruturas e identificadores físicos de armazenamento continuam intactos. Os nomes internos dos auxiliares ART e consumidores de typedefs de contas já existentes passam a usar PGS sem alterar comportamento ou layout. Os testes de pré-validação exercitam a prioridade de `PGS_VERSION` e a alternativa legada.

## Etapa 14 — nomes ativos restantes e inventário integral

Nomes PGS passam a ser usados em threads Java, tags de diagnóstico, caches descartáveis, descrições de interface e consumidores de tipos/macros nativos com aliases existentes. A limpeza de diretórios temporários aceita as duas grafias. As opções de compilação não confidenciais aceitam os nomes PGS e mantêm os aliases de ativação anteriores. Não há mudanças nos identificadores de armazenamento persistente, package IDs, configuração de assinatura ou exports da ABI. O [inventário de textos rastreados](../PGS_REMAINING_REFERENCES.json) registra as referências restantes ao nome original por arquivo e categoria; é um retrato para revisão, não uma declaração de que toda ocorrência restante seja necessária. Conteúdo binário e arquivos temporários de migração são excluídos. Créditos legais e registros históricos permanecem intactos. Exige-se a validação geral de fontes e ABI antes da integração.


## Etapa 15 — aliases nativos e auditoria reproduzível

Os aliases de fonte para valores de enumeração e tipos de ponteiros de função equivalentes preservam o tipo da enumeração, valores numéricos, assinaturas de ponteiros, tags de estruturas, layout, exports da ABI e strings de resolução dinâmica. A regressão C++17 existente passa a verificar também a identidade do tipo das enumerações e que os enumeradores legados não viraram macros. Auxiliares privados e referências ativas equivalentes usam a grafia PGS. Nenhum comportamento de recurso nativo ou política de proteção é alterado.

Execute `python -B tools/pgs_reference_inventory.py --summary` em um checkout Git para uma nova varredura somente de leitura. Sem `--summary`, são exibidas as contagens por arquivo. O CI geral executa o teste de inventário; o retrato versionado é um delta exato do inventário anterior, ainda não uma varredura independente. A regra de texto UTF-8/NUL é explícita; diferenças de escopo devem ser reconciliadas antes de comparar retratos.

### Classificação do trabalho restante

- Substituível agora: constantes e tipos de fonte com equivalência verificada, auxiliares privados e rótulos de interface ou diagnóstico que não sejam contratos.
- Migração coordenada: getters nativos ocultos e resoluções weak/dinâmicas, nomes de bridges JS, prefixos de métodos do reescritor DEX e nomes de objetos em execução. Revisar todos os produtores, consumidores e testes antes de modificar.
- Compatibilidade: identificadores físicos de contas e preferências, AndroidKeyStore, canais de notificação, IDs dos aplicativos/módulos Root e Preview, marcadores de rejeição de entradas antigas, configuração de assinatura e alternativas de ambiente. Preservar até haver migração compatível explícita.
- Atribuição/licença e histórico: preservar avisos originais e registros anteriores de releases/builds.
- Testes de compatibilidade: preservar asserções dos nomes antigos quando comprovarem fallback, identidade da ABI, rejeição de entrada ou continuidade dos dados. Consumidores comuns podem usar nomes PGS equivalentes verificados.

As contagens restantes não comprovam que todas as ocorrências sejam necessárias. Release completo assinado, insumo autorizado e teste em dispositivo físico são etapas separadas. Este lote não altera APK nem registro de emissão.

## Etapa 16 — consumidores da fábrica principal e reconciliação do inventário

O carregador JS ativo resolve primeiro `pgs_native_api` e usa o export legado existente somente se o símbolo principal estiver ausente. Mantém as verificações anteriores da ABI e não usa fallback diante de erro de validação da ABI. Os testes nativos funcionais passam a resolver a fábrica PGS; um teste de integração explícito verifica ponteiros v1/v2 idênticos e rejeição de versões incompatíveis pelos dois exports. O teste JS verifica busca principal, alternativa legada, ausência dos símbolos e rejeição da ABI. Nenhum export ou comportamento dos recursos é alterado.

O CI independente da etapa 15 registrou 2.468 referências em 539 arquivos, entre 1.031 arquivos de texto UTF-8 e 2.106 caminhos rastreados (inventário excluído). O inventário versionado por deltas registrava 2.477 referências. A divergência é de nove referências e um arquivo com ocorrências na categoria nativa; a causa precisa ainda não foi estabelecida. A etapa 16 preserva os deltas exatos do inventário versionado e acrescenta `--compare-snapshot` para exibir os caminhos e contagens divergentes da nova varredura, inclusive no CI. Reconciliar o escopo antes de declarar uma nova contagem independente exata. Licenças, chaves de dados, rejeição de entradas antigas, histórico de releases e contratos de assinatura permanecem intactos. Não implica emissão de APK nem validação física.

## Etapa 17 — auditoria pelo índice Git e consumidores restantes da fábrica

O CI da etapa 16 identificou uma única divergência na varredura da cópia de trabalho: nove referências em `pgs/native/account_host.cpp`. A primeira leitura textual do conector sugeriu UTF-8 válido, mas a solicitação do blob bruto rejeitou o fonte e as varreduras do índice e da cópia de trabalho no CI o excluíram. O inventário segue o escopo reproduzível do CI; os bytes originais do fonte não são reescritos. O arquivo fonte é preservado; a auditoria passa a ler os blobs indexados com `git cat-file --batch`, sem depender de filtros de checkout ou alterações geradas pelos testes. Um modo separado verifica a cópia de trabalho e informa divergências; as contagens por arquivo do índice devem coincidir com o inventário versionado. Um teste em repositório Git temporário comprova que arquivos não rastreados e alterações locais não afetam a contagem indexada.

Os testes C++ funcionais restantes com busca direta da fábrica antiga foram migrados para a fábrica principal. A cobertura explícita de paridade da ABI e os símbolos de ligação dos testes internos permanecem intactos. Nenhuma implementação nativa de recursos, comportamento do jogo, chave persistida, licença, assinatura, versão ou APK foi alterada. Uma pequena limpeza de documentação e identificação de build atualiza também o diretório fonte vigente e o agente HTTP.

## Etapa 17 consolidada — migração de identidade em massa

Uma única pull request coordenada migra 63 nomes de fábricas nativas privadas, suas declarações, definições, referências no registro, buscas internas por símbolo e consumidores de teste. O escopo revisado de fontes nativos, testes, Java e ferramentas de build compreende 391 caminhos. Os 14 arquivos JavaScript afetados de runtime e diagnóstico e os 15 testes JS correspondentes adotam a identidade PGS. A fábrica pública de compatibilidade, as dependências nativas do fonte de contas excluído da varredura e o contrato de código de erro do snapshot traduzido são preservados. O teste IV prioriza a fábrica principal e recorre à antiga apenas quando o mock legado não disponibiliza a principal. Assinatura, chaves persistentes, licenças, atribuição original, lógica de recursos e dados de releases estão fora desta renomeação. Todas as alterações são agrupadas antes de uma execução geral do CI; não se declara compatibilidade nem validação em aparelho antes dos testes.

## Etapa 18 — limpeza consolidada da identidade no código

As chamadas nativas diretas usam a grafia principal PGS. Oito funções auxiliares privadas encaminham a versão sem mudanças para os símbolos internos existentes; nenhum novo export dinâmico, layout de tabela ou comportamento de recurso é introduzido. Os símbolos originais permanecem disponíveis para objetos antigos, testes com ligação fraca e o arquivo excluído da auditoria UTF-8. Mais aliases de tipos e constantes, macros locais, comentários atuais, nomes de diretórios temporários e textos do instalador usam PGS. Caminhos físicos do módulo root, saída de comandos, identidades Android, armazenamento persistido, canais de notificação, assinatura, histórico e atribuição de licença permanecem intactos. Testes nativos sintéticos e verificações dos textos do instalador validam a nova grafia. O CI da etapa 17 reconciliou de forma independente as 1.728 referências sem divergências entre índice e checkout. A etapa 18 usa deltas exatos até a confirmação pelo CI geral.

## Etapa 19 — migração em massa da identidade principal

Os tipos PGS são agora as definições originais, e os aliases typedef antigos apontam para essas definições. Sete getters privados passam a ser implementados e consumidos com os nomes PGS, preservando funções auxiliares para consumidores de código anteriores. O arquivo fonte do account-host foi mantido byte a byte porque o texto reconstruído pelo conector não coincidiu com o hash do blob Git original; suas chamadas existentes continuam pelas interfaces de compatibilidade. A fábrica pública conserva ambos os exports, e os consumidores de câmera/spawn priorizam a fábrica principal. A grafia do getter privado gym-repeat, tags de diagnóstico selecionadas, nomes internos de objetos de interface e consumidores e testes identificados foram atualizados em conjunto. Nenhum comportamento do jogo, layout de tabela, dado persistido, assinatura, licença original ou APK foi alterado. Nomes de tags C++ antigos não são garantidos; os aliases typedef e a ABI binária pública permanecem. O CI geral deve confirmar a candidata antes da integração.

### Limpeza consolidada dos nomes atuais

Os novos assets de modo usam `pgsVersion`. O verificador da candidata exige esse campo e rejeita metadados legados contraditórios; o verificador histórico continua aceitando assets antigos com versão correta. As instruções de pré-requisitos e os comprovantes de ambiente gerados usam as variáveis PGS, preservando os fallbacks de entrada. Descrições atuais dos headers, nomes internos de diagnóstico e testes sintéticos correspondentes foram atualizados em conjunto. As configurações do repositório descrevem os caminhos atuais, não o layout aposentado. Sem mudanças na assinatura, nos APKs existentes, identificadores de armazenamento protegidos, exports públicos da ABI ou avisos legais originais. O inventário textual restante inclui registros históricos, procedência, contratos preservados e seus testes. Não use busca com zero resultados como prova de migração nem apague evidências para reduzir um contador. Toda ocorrência ainda não classificada precisa de revisão antes de afirmar que todas as referências substituíveis foram removidas.

## Revisão final de identidade após a etapa 19

A PR #61 está integrada, com CI geral aprovado no head e CI de fontes pós-merge aprovado. A nova limpeza usa nomes principais PGS nas chamadas diretas da câmera e nos testes do account-host, além de atualizar a marca nos diagnósticos do carregador root sem alterar marcadores físicos ou fluxo de controle. As notas antigas da migração nativa estão identificadas como histórico, não como instruções de compilação atuais.

O inventário indexado agrupa todos os arquivos restantes por finalidade de retenção ou dependência de migração ainda não resolvida. É uma triagem por arquivo, não prova de que cada ocorrência individual seja indispensável. Preserve a atribuição original, registros históricos, verificações explícitas de legado, identidades instaladas, armazenamento criptografado, assinatura e compatibilidade da ABI. Interfaces de ligação fraca ainda exigem revisão coordenada para retirar os nomes antigos. A implementação do account-host permanece fora da auditoria UTF-8 estrita; não a reescreva usando texto reconstruído pelo conector. O feed externo precisa de um substituto autorizado e verificado antes de alterar o endpoint; o trabalho do feed independente está na PR #62. Nenhum APK foi gerado ou instalado nesta revisão.

## Limpeza das abreviações da identidade nativa

O inventário anterior do nome completo não contabilizava as grafias separadas `PGS_`, `pgs_` ou `PgsCamelCase`. A auditoria ampliada de texto indexado agora informa essas formas separadamente, com contagem exata por arquivo; a série anterior do nome completo permanece disponível para comparação. Este lote exclusivamente de código migra 258 nomes distintos e 1.600 usos nos headers de contas, spin, spawn, map tap, map POI, VGP auxiliar e batalhas e nos consumidores identificados. Valores de constantes e enums, membros de estruturas, verificações de layout, versões de API e exports públicos permanecem inalterados. Os tipos C++ privados são reconstruídos em conjunto; retirar grafias antigas não implica compatibilidade com objetos privados compilados separadamente. O blob original do account-host não pode ser verificado pelo texto reconstruído do conector e permanece intacto. Seus dezesseis nomes legados de constantes identificados continuam como aliases de código em `account_source_compat.h`. A migração das abreviações ainda não é exaustiva: o inventário geral do CI estabelecerá a contagem restante e validará os nomes propostos. A branch do feed independente, assinatura, dados instalados, artefatos de release e avisos originais permanecem intactos.

## Retirada dos aliases privados e identidade dos novos artefatos

As etapas anteriores de compatibilidade são históricas. O PR #65 remove 125 aliases equivalentes de tipos/constantes C/C++ e 12 funções privadas de encaminhamento, atualiza seus consumidores e verifica os tamanhos, alinhamentos e valores LP64 originais. A fábrica binária pública e as verificações de rejeição de entradas antigas permanecem. Novas bridges DEX usam o prefixo PGS. Novos backups de configurações usam o esquema versão 2, com nomes de grupos PGS; backups versão 1 continuam importáveis. Identificadores físicos das preferências e do cofre criptografado permanecem inalterados. Uma versão antiga que entende apenas o esquema 1 não lê exportações do esquema 2. O cache Dobby migra seu marcador descartável somente após verificar o arquivo e os fontes. Os recibos do controle Root usam PGS, preservando os caminhos instalados e o marcador Off. CI integral, APK assinado e teste físico continuam sendo verificações distintas.

## Identidade final dos fontes e limite da candidata

Novos payloads do runtime Root usam o diretório descartável PGS. Os diretórios fixos de cache anteriores não são apagados nem renomeados; identificadores de módulos instalados e o marcador Off do usuário permanecem inalterados. A entrada binária pública de compatibilidade, os identificadores de armazenamento e criptografia de perfis existentes, os canais de notificação, o reconhecimento de entradas históricas e os aliases de configuração da assinatura são preservados deliberadamente. Alterar esses contratos exige migração independente e testes em aparelho real. A retirada dos nomes de código-fonte é distinta da retirada desses contratos.

Para a próxima compilação completa, use o workflow existente de validação manual autorizada da v0.0.3 na main após aprovação da CI. Ele verifica a candidata completa assinada e envia somente recibos; não distribui arquivos do jogo nem declara aprovação física. O repositório é público. Para testar um APK completo em aparelho, um mantenedor autorizado deve compilar e conservar a candidata assinada em ambiente controlado. Não avance o ledger de versão publicada nem declare instalação/login aprovados sem evidência correspondente. Rascunhos, chaves e branches de backup anteriores permanecem preservados.
