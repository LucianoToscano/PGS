# Auditoria da identidade PGS — 27/11/2026

O PGS é o aplicativo Android **Pokémon GO** com package `com.nianticlabs.pokemongo` e certificado SHA-256 **D9:5C:6B:DF:CB:D9:1D:C5:C9:CD:E6:98:48:7C:88:E4:99:47:71:A4:75:E4:EF:DE:45:67:B8:D5:F4:4E:96:CF**. Outros aplicativos independentes instalados no dispositivo não devem ser modificados.

## Migrado na PR #33

- Textos da UI e notificações PGS, inclusive contador de encontros, feed Shundo, GPX e logcat
- Onze catálogos de idioma de 1.332 textos com rótulos PGS e tabelas Java regeneradas; entradas antigas de tradução aceitas por alias durante a transição
- Web/README, nomes de pacote web, títulos visíveis e manifesto de preview de testes
- Script de anúncio de release Discord restrito ao arquivo `PGS.vX.Y.Z.apk` do repositório PGS e presença de `SHA256SUMS.txt`
- Sem reutilização do webhook, canal ou cargo Discord antigo: configurar `PGS_DISCORD_RELEASE_WEBHOOK` e `PGS_DISCORD_CHANNEL_ID` separadamente
- Backups novos com formato `PGS settings`; backups de versões antigas ainda aceitos sem reescrever dados
- Política de release falha se o ledger de `versionCode` PGS desaparecer, em vez de produzir um instalador com identificação externa
- Arquivo histórico das releases upstream explicitamente identificado para que o usuário não instale o binário errado

## Referências legadas intencionalmente preservadas

Não é seguro fazer substituição global nas chaves ou símbolos de protocolo. Nesta etapa permanecem:

- Diretório de fonte `pgrazor/`, classes Java `dev.pgrazor`, componentes DEX e paths `assets/pgrazor/`
- Bibliotecas `libpgrazor-*.so`, símbolos nativos JNI, interfaces JavaScript internas `PGRazorNative*`, variáveis de build `PGRAZOR_*`
- Preferências salvas como `pgrazor-map`, `pgrazor-overlays`, IDs e nomes internos de módulo Root, e chaves antigas de backup
- Identificadores de testes, o tema antigo do site (já migrado) e a logo **dentro do jogo** com o botão original, mais a lógica do joystick
- Histórico de contribuição, licenças e referências precisas ao projeto-base e forks terceiros, para preservar atribuição

Esses identificadores técnicos não são *nomes do aplicativo instalado* e renomeá-los sem migração, JNI e testes de atualização pode impedir o PGS de abrir ou apagar configurações. O Root não é publicado como APK PGS.

## Verificação

Rodar `python -B tools/pgs_branding_audit.py` ou `python -B tools/check.py`. O gate CI bloqueia novos textos antigos em superfícies públicas, links de APK upstream e regressão de versão/certificado.

A PR não publica APK automaticamente. A próxima nova build completa deverá ser `v0.0.2`, com `versionCode >= 2026111605`, o mesmo certificado PGS e testes físicos pendentes.

## Preparação da v0.0.2

O arquivo `.github/FUNDING.yml` deixou de apontar para o Ko-fi do projeto original (não há conta de doação PGS cadastrada). O gate CI agora reprova o reaparecimento desse destino. A candidata `v0.0.2` usa o APK completo assinado de `v0.0.1` como entrada, recompila os controles Java com os nomes PGS, mantém DEX do jogo e bibliotecas nativas inalterados e exige `versionCode=2026111605` e o mesmo certificado. Instalação/login sobre o PGS anterior ainda dependem de teste físico. Nenhum identificador `dev.pgrazor`, recurso `assets/pgrazor` ou logo/joystick interno foi renomeado.
