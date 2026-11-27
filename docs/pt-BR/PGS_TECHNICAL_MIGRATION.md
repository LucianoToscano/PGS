# PGS — migração dos nomes internos: Etapa 1

Estado: migração do código iniciada na branch `refactor/pgs-native-build-names-phase1`. Esta etapa **não** publica um novo APK assinado.

[🇺🇸 English](../en/PGS_TECHNICAL_MIGRATION.md) · [🇧🇷 Português (Brasil)](PGS_TECHNICAL_MIGRATION.md)

## O que está sendo renomeado

- Arquivos principais: `pgrazor_native.cpp` → `pgs_native.cpp`; `pgrazor.map` → `pgs.map`.
- Cabeçalhos: `pgrazor_internal.h` → `pgs_internal.h`; `pgrazor_native_api.h` → `pgs_native_api.h`, com arquivo de encaminhamento para includes antigos.
- Script de exportação ART: `pgrazor-art.map` → `pgs-art.map`.
- Alvos internos do CMake: `pgrazor_core` → `pgs_core` e `pgrazor_art` → `pgs_art`.
- Novas variáveis `PGS_NATIVE_PILOT`, `PGS_NATIVE_DOWNLOAD`, `PGS_ART_NDK` e `PGS_NATIVE_DEPS`, mantendo os aliases anteriores.
- Novo comando de Windows `pgs.cmd`; o antigo `nonroot.cmd` continua funcionando como encaminhamento.

## Compatibilidade obrigatória

Os binários `libpgrazor-core.so` e `libpgrazor-art.so`, a função nativa exportada `pgrazor_native_api`, o namespace Java `dev.pgrazor` e os caminhos `assets/pgrazor` continuam temporariamente iguais, pois são referenciados pelo carregamento do aplicativo. A troca integral deles exige atualizar os consumidores ao mesmo tempo e criar testes de compatibilidade.

**Nada altera** o nome instalado **Pokémon GO**, o package **`com.nianticlabs.pokemongo`**, o certificado PGS, o `versionCode` ou os dados de instalações anteriores.

A etapa será verificada com testes de código e compilação. Não considerar que houve teste físico ou geração de APK completo nesta PR.

## Próximas etapas

Migrar gradualmente classes Java/JNI, binários, arquivos de execução e preferências salvas, com aliases, testes e preservação de dados. A autenticação Google precisa de credenciais OAuth próprias autorizadas, sem inventar IDs. Somente após compilação completa e teste de atualização sobre o APK instalado será possível lançar uma versão.

Acompanhe o restante na [issue #38](https://github.com/LucianoToscano/PGS/issues/38). O histórico e os créditos de licença permanecem preservados.

## Etapa 2 — migração dos includes C++

Os módulos C++ do projeto e os testes nativos passam a incluir `pgs_native_api.h`, no lugar de `pgrazor_native_api.h`. O cabeçalho de compatibilidade antigo continua disponível para builds anteriores. Uma nova verificação automática impede que includes antigos retornem ao código.

Esta etapa não altera os símbolos exportados, os nomes de bibliotecas `.so`, o identificador Android, o certificado ou as preferências salvas. Aprovação dos testes de código **não** significa APK completo recompilado ou atualização física aprovada.

## Etapa 3 — fábrica nativa PGS sem perder compatibilidade

- A nova função C exportada `pgs_native_api(uint32_t)` é o nome principal. A função antiga `pgrazor_native_api(uint32_t)` continua presente e encaminha à nova. As duas devolvem **as mesmas tabelas imutáveis v1/v2** para as versões válidas e `null` para versões incompatíveis.
- O script `pgs.map`, a verificação de símbolos ELF e o teste nativo exigem exatamente **três símbolos** exportados: `JNI_OnLoad`, `pgs_native_api` e `pgrazor_native_api`. Os demais ficam ocultos.
- Constantes, códigos de erro e tipos de funções podem ser escritos como `PGS_*` / `pgs_*`. Os nomes antigos funcionam como aliases e o tamanho e a ordem dos campos das tabelas v1/v2 não mudam.
- O Android ainda carrega `libpgrazor-core.so` e `libpgrazor-art.so`, e os módulos Java/JNI podem continuar usando o nome antigo. Não são alterados o pacote Java `dev.pgrazor`, backups, dados, pacote Android `com.nianticlabs.pokemongo`, chave PGS ou `versionCode`.
- Esta etapa depende de testes de código e símbolos nativos. **Não** é uma compilação de APK completo nem comprova atualização física. O restante permanece na [issue #38](https://github.com/LucianoToscano/PGS/issues/38).

## Etapa 4 — nomes PGS no motor de hooks C++

- As implementações internas principais passam a ser `pgs_hook`, `pgs_unhook`, `pgs_instrument` e `pgs_hook_diag`. Os nomes antigos `pgrazor_*` continuam funcionando como encaminhamento, usando **o mesmo mutex e registro Dobby**.
- Os tipos `PgsHookDiag` e `PgsPaddingRanges` conservam o layout e os cálculos originais. O núcleo chama os nomes PGS e o teste de ilhas ARM valida ambas as interfaces.
- Os logs de erro do Android passam a usar a etiqueta `PGS`. Esta etapa não exporta novos símbolos ELF, não muda arquivos `.so`, package, certificado, assinatura, nem cria hooks adicionais ou APK completo.
- A migração de Java/JNI, bibliotecas, caminhos e preferências exige verificação de instalação física e continua na [issue #38](https://github.com/LucianoToscano/PGS/issues/38).

## Etapa 5 — opções não confidenciais de compilação com nomes PGS

O compilador Java em `pgs/build.py` agora usa prioritariamente `PGS_VERSION`, `PGS_BUILD_TOOLS` e `PGS_ANDROID_PLATFORM`. Os aliases `PGRAZOR_*` continuam aceitos para manter os workflows existentes e as compilações antigas. Se ambas as opções estiverem definidas, a versão PGS não vazia prevalece; valores vazios utilizam o alias.

As variáveis de chave e senhas `PGRAZOR_KEYSTORE`, o arquivo da chave, os caminhos de preview/DEX, o pacote Android, o certificado definitivo e o registro de `versionCode` **não mudam** nesta etapa. A alteração não gera outra chave. Um teste isolado verifica padrões, aliases, precedência e versão sem executar assinatura ou Android SDK. Testes de fonte aprovados não comprovam APK completo nem instalação no celular.

## Etapa 6 — consumidores diretos de hooks (alimentação de companheiro e itens)

Os módulos de produção `buddy_feeding.cpp` e `items.cpp` passam a chamar diretamente `pgs_hook` (dois e cinco pontos de chamada, respectivamente). Os respectivos simuladores isolados para Linux definem o símbolo principal correspondente; os testes existentes de compilação e execução verificam os consumidores migrados sem depender do encaminhamento antigo. O teste de identidade também impede o retorno acidental de `pgrazor_hook` nesses pontos.

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
