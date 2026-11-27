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
