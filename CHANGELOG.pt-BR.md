# PGS — Registro de alterações

**Idiomas:** [🇺🇸 English](CHANGELOG.md) · 🇧🇷 Português (Brasil)

Este registro acompanha **somente** as versões do PGS. Os documentos históricos da base original permanecem disponíveis pelo histórico Git e pelos avisos legais, mas não são releases do PGS.

## Em desenvolvimento — segunda auditoria

- Opções gráficas restauram apenas valores ainda controlados pelo módulo e restauram o asset URP anterior antes de modificar outro. Metadados opcionais de plantas não bloqueiam os demais controles. Diagnóstico informa FPS-alvo, hooks ativos e manutenção lenta sem alegar medição de FPS real.
- Captura no mapa mantém visível um encontro não confirmado, impedindo pedidos automáticos duplicados. Apenas captura ou fuga confirmada autoriza remover o objeto restante. Histórico de segurança cheio informa a alternativa manual sem descartar resultados incertos.

- Auto Raid não avança recompensas por trás de outra janela. Ao fechar o aviso manualmente, o fluxo normal pode continuar; um prazo limitado informa o bloqueio. A classe exata da janela Lucky Egg e a recusa automática ainda não foram verificadas.
- Evita ações duplicadas de recompensa no mesmo tick e repetição da confirmação final; preserva as regras de revogação e consumo da sessão.
- Limita consultas de prontidão do mapa à cadência de descoberta; um novo bloqueio tem seu próprio prazo, sem herdar o tempo de busca anterior.
- Skip Cutscenes restaura a tela de recompensas quando outra janela assume a entrada. Fixtures de regressão cobrem essas situações; não há alegação de teste físico ou medição de FPS.

## v0.0.6 — 28/11/2026

- Atualização do feed de Hundos a cada 60 segundos, referências externas corrigidas e testes de regressão do Worker.
- Melhorias no build permanente, monitoramento da origem e retenção de 90 dias dos backups de código; recuperação de falhas temporárias nas dependências Maven fixadas.
- Publicados APK sem Root assinado (versionCode `2026111609`), instalador Root e módulo, com recibos e checksums.
- Capturas do responsável confirmam atualização interna da v0.0.5 e preservação da sessão e das configurações. Nove pendências da primeira auditoria aceitas pelo responsável; cinco itens funcionais/Root não possuem registros detalhados separados.
- [Notas bilíngues completas](https://github.com/LucianoToscano/PGS/releases/tag/v0.0.6).

## v0.0.5 — 28/11/2026

- APK Android completo recompilado e assinado, com pacote e certificado existentes; versionCode `2026111608`.
- Feed de hundos do PGS configurado e login Google pelo navegador habilitado no build.
- Instalação e abertura confirmadas pelo responsável do projeto; login Google e atualização interna ainda não verificados separadamente.
- Release estável do GitHub para o atualizador interno existente.

## Em desenvolvimento

- Identidade pública PGS consolidada no README, site, arte oficial, contribuição e documentação.
- Preservação das interfaces JNI, caminhos de runtime e preferências existentes até migração compatível e testada.
- Testes automáticos para impedir regressão de identidade, versão ou links de instalação.

## v0.0.2 — Candidata completa

- Pokémon GO `0.439.0`; pacote `com.nianticlabs.pokemongo`; `versionCode=2026111605`.
- Reorganização de identidade PGS, traduções e links públicos sem alterar a assinatura existente.
- APK completo e assinado: https://github.com/LucianoToscano/PGS/actions/runs/45980315394
- SHA-256 do APK: `91865f6242519091a771617f962f17620405624a4a56addec0909d2cdf6b68c1`.
- Release privado em rascunho. **Ainda não há confirmação de instalação e login em aparelho real.**

Consulte [LICENSE](LICENSE) e [THIRD_PARTY.md](THIRD_PARTY.md) para os avisos e condições legais.
