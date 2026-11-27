# Idiomas da interface PGS

## Como mudar

Abra **Settings → Display & Performance → Language → PGS language**, escolha o idioma e feche completamente o jogo. Ao abrir novamente, a interface PGS usa a seleção salva.

Em português, o caminho é **Configurações → Exibição e desempenho → Idioma → Idioma PGS**. A linha informa que a mudança terá efeito após reiniciar o jogo. A troca não encerra o jogo automaticamente.

| Opção no seletor | Idioma | Código salvo |
| --- | --- | --- |
| Sistema / System | Seguir o dispositivo | `system` |
| Deutsch | Alemão | `de` |
| English | Inglês | `en` |
| Español | Espanhol | `es` |
| Français | Francês | `fr` |
| Português | Português brasileiro | `pt-BR` |
| Русский | Russo | `ru` |
| Italiano | Italiano | `it` |
| 繁體中文 | Chinês tradicional | `zh-Hant` |
| Nederlands | Holandês | `nl` |
| ภาษาไทย | Tailandês | `th` |
| 한국어 | Coreano | `ko` |

Os nomes dos idiomas aparecem na própria língua, para facilitar a recuperação de uma seleção feita por engano. A opção Sistema é traduzida para o idioma ativo.

## Preferência e compatibilidade

- A escolha é global para o aplicativo. Trocar a conta do jogo ou ativar/desativar as configurações compartilhadas não troca o idioma.
- Uma instalação sem escolha salva segue o sistema. Idiomas do dispositivo não disponíveis usam inglês. Todas as variantes de português usam o catálogo brasileiro; as variantes de chinês usam o catálogo tradicional disponível.
- A escolha é gravada de forma atômica em `pgs-language-v1.properties`, separada dos perfis de conta. Falhas de gravação mantêm a escolha anterior e apresentam uma mensagem.
- Exportações explícitas de configurações incluem `pgsLanguage`. Importar um backup antigo sem esse campo preserva a escolha atual. Valores inválidos são recusados antes da aplicação do backup.
- A seleção importada também exige reinício. O tradutor não muda durante a sessão, inclusive após recriação de uma Activity.
- A mudança usa apenas o tradutor do PGS: não modifica `Locale.setDefault`, os recursos do jogo, coordenadas, formatos de protocolo ou identificadores internos.

Menus, botões, opções fixas, descrições de acessibilidade, confirmações e mensagens locais de interface usam os catálogos. Nomes de Pokémon, contas, favoritos e rotas, respostas de serviços externos, erros técnicos e registros de diagnóstico mantêm seus valores originais. A opção não altera o idioma do Pokémon GO nem cria uma tradução dos nomes de Pokémon nos filtros.

## Busca de configurações

A busca usa simultaneamente os rótulos e descrições traduzidos e seus equivalentes em inglês. Os resultados abrem os mesmos controles e mantêm os mesmos identificadores. A normalização de busca ignora acentos latinos, preservando sinais relevantes nos demais alfabetos.

## Manutenção das traduções

Os arquivos editáveis estão em `pgs/i18n/*.json`. `en.json` contém as chaves canônicas em inglês, com valor idêntico à chave. Todos os demais catálogos precisam conter exatamente o mesmo conjunto de chaves.

Depois de editar os JSONs, execute na raiz do repositório:

```sh
python -B tools/i18n_catalog.py
python -B tools/check.py
```

O gerador cria `I18nCatalog.java` e uma classe por idioma em `pgs/src/dev/pgs`. Esses arquivos são versionados para que a compilação Android funcione offline, sem depender dos recursos do APK hospedeiro. A verificação de CI rejeita classes geradas desatualizadas, chaves ausentes/extras, duplicações e alterações incompatíveis nos marcadores de formato.

Use `I18n.t` para textos fixos e `I18n.format` para mensagens com dados. Prefira argumentos indexados (`%1$s`, `%2$d`) quando a tradução puder precisar de outra ordem. Preserve os marcadores, os tipos dos argumentos, a precisão e `%%`. Os dados passados como argumentos permanecem opacos. `I18n.options` é exclusivo de listas fixas da interface; não deve ser aplicado a nomes ou dados do usuário.

Mantenha os códigos de preferência, nomes de campos JSON, fases de máquinas de estado, URLs, comandos, bitmasks e identificadores nativos em suas formas canônicas. Traduza os rótulos no ponto em que são exibidos. Campos de busca conservam separadamente a chave canônica e o texto exibido.

## Verificação

Os testes exercitam seleção e fallback, persistência em um novo processo, preferência independente das contas, importação de backups antigos, busca bilíngue, argumentos preservados e formatos inválidos. O teste de catálogos compila as tabelas reais em Java e verifica o conteúdo de todos os idiomas após a geração.

A compilação Android e a verificação de assinatura e empacotamento complementam esses testes. A instalação, a legibilidade em cada tamanho de tela, a leitura por tecnologias assistivas e a execução do jogo precisam ser observadas em um dispositivo; testes sem dispositivo não substituem essas observações.
