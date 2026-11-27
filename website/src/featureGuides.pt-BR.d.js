export const guidesD = {
  research: {
    title: 'Pesquisa de campo',
    summary: 'Resgate pesquisas concluídas automaticamente, apague tarefas indesejadas e capture encontros de pesquisa pendentes.',
    where: 'Menu rápido > Pesquisas ou Configurações > Automação > Pesquisa de campo.',
    steps: [
      'Abra Pesquisas no Menu rápido ou em Configurações > Automação.',
      'Ative Resgatar pesquisas concluídas automaticamente para receber tarefas cujo objetivo já foi cumprido.',
      'Ative Apagar tarefas selecionadas e marque quais deseja excluir. Elas são agrupadas em Itens, Encontro e Evento; use a busca para localizar.',
      'Ative Capturar encontros de pesquisa automaticamente para capturar recompensas pendentes sem abrir a tela de encontro.',
    ],
    notes: [
      'Pesquisas especiais, temporizadas e de história continuam manuais, e tarefas bônus de ginásios nunca são apagadas.',
      'As tarefas aparecem na lista conforme o jogo as oferece durante a execução do PGS.',
      'A captura automática usa bola e arremesso VGP+. Cada tentativa consome bola; os Pokémon seguem suas regras de transferência, inclusive Manter todos. Funciona junto com VGP.',
      'Se abrir manualmente um encontro de recompensa, Arremesso automático deixa a captura para você.',
    ],
  },
  'hide-overlay': {
    title: 'Ocultar painel',
    summary: 'Oculte todos os controles, indicadores e textos de IV do PGS para o jogo parecer a versão padrão.',
    where: 'Menu rápido > Ocultar painel.',
    steps: [
      'Abra o Menu rápido, toque em Ocultar painel e confirme.',
      'Botões, barras de status, mensagens e IVs exibidos pelo PGS desaparecem.',
      'Toque na tela com três dedos ao mesmo tempo para exibi-los novamente.',
    ],
    notes: [
      'Há uma confirmação antes de ocultar, evitando que um toque acidental esconda tudo.',
    ],
  },
  'livepokemap-feeds': {
    title: 'Feeds: LivePokeMap e PoGoCoordinates',
    summary: 'Consulte avistamentos remotos do LivePokeMap (assinatura própria) ou PoGoCoordinates (login Discord ou convidado).',
    where: 'Menu rápido > Feeds.',
    steps: [
      'Abra Feeds e escolha LivePokeMap ou PoGoCoordinates. Cada serviço usa sua própria autenticação.',
      'LivePokeMap: contrate assinatura separada, entre com sua conta e consulte Pokémon, Poképaradas, ginásios, reides e estações remotas. Em Filtros, escolha espécies, faixas de IV/nível, tamanho, exceções, classificação PvP e brilhantes/fundos. Preferências são salvas localmente. Apenas PvP mostra só Pokémon até a classificação máxima nas ligas selecionadas, ignorando IV, nível e tamanho.',
      'PoGoCoordinates: entre pelo Discord para limites maiores ou continue como convidado. Pesquise Pokémon, reides, pesquisas, clima, Rocket e Pontos de Poder por IV, nível, PvP e outros critérios.',
      'Selecione um resultado para Mapa, Caminhar ou Teleportar.',
    ],
    notes: [
      'LivePokeMap exige assinatura ativa paga separadamente; não está incluído. A aba Meus brilhantes foi removida porque o serviço não a oferece mais.',
      'O token de sessão é criptografado pelo Android Keystore e a senha nunca é salva; Sair remove o token.',
      'A atualização para quando o feed fecha ou o aplicativo sai de primeiro plano. Nas builds candidatas, também pausa em Global; Atualizar e mudanças de filtros/raio ainda consultam quando o servidor permite. Avistamentos remotos expiram e não são locais que o jogo necessariamente carregou.',
      'Ambos os feeds usam a interface web observada de cada serviço, que pode mudar. O acesso depende de sua conta e do funcionamento desses serviços.',
    ],
  },
  'settings-search': {
    title: 'Busca de configurações',
    summary: 'Localize uma opção por nome, descrição ou palavra-chave e acesse-a diretamente.',
    where: 'Configurações > Buscar configurações (campo no topo da tela principal).',
    steps: [
      'Abra Configurações. O campo Buscar configurações fica no alto da página inicial.',
      'Digite parte do nome, descrição ou palavra comum como “gps falso” ou “modo claro”.',
      'Toque em um resultado para abrir sua página e rolar até a opção.',
    ],
    notes: [
      'Limpe o campo para retornar à lista de páginas.',
      'A tela principal organiza as páginas em Jogar (Localização e mapa, Captura, Pokémon e transferência, Go Plus, Batalhas, Companheiro), Automação (Automação e Eventos) e Aplicativo (Exibição e desempenho, Contas e backup).',
    ],
  },
  'settings-backup': {
    title: 'Configurações, temas e backup',
    summary: 'Temas claro/escuro, escala dos painéis, bloqueio visual de controles dependentes e exportação/importação JSON.',
    where: 'Configurações > Exibição e desempenho > Interface (Tema escuro, Escala) e Entradas do menu rápido; Contas e backup > Contas e dados > Exportar/importar configurações.',
    steps: [
      'Ative/desative Tema escuro em Exibição e desempenho > Interface ou toque no ícone de tema no topo da página para alternar entre claro e escuro.',
      'No mesmo grupo, ajuste Escala da interface para 100%, 75%, 50% ou 25%, incluindo inicializador, menu rápido, joystick, temporizador e painéis.',
      'Em Exibição e desempenho > Entradas do menu rápido, mostre ou oculte qualquer uma das 13 opções. Isso só afeta a visibilidade, não ativa/desativa recursos; Configurações sempre fica disponível. A escolha é salva por conta e em backups.',
      'Arraste o temporizador de espera, relógio local, ícone VGP e botão Manter todos para reposicionar.',
      'Em Contas e backup > Exportar/importar configurações, salve um JSON e restaure em outro celular ou após reinstalação.',
    ],
    notes: [
      'Quando o controle principal está desligado, dependentes ficam cinza mas preservam as escolhas (por exemplo VGP+ sob o painel VGP e opção de menor PC sob Colocar automaticamente).',
      'O backup inclui preferências, velocidade, favoritos, camadas do mapa, filtros e perfis dos feeds e posições dos painéis.',
      'Tokens de login, localização atual, histórico de espera e rotas ativas ficam de fora; a importação deixa o VGP desligado.',
      'Sessões de conta são criptografadas no dispositivo e nunca fazem parte de exportações de configurações nem de backups Android.',
    ],
  },
  'pgs-root': {
    title: 'PGS Root (não lançado)',
    summary: 'A versão PGS v0.0.2 é somente sem root. O instalador Root de outro projeto não é uma atualização do PGS.',
    where: 'O PGS oferece atualmente um APK ARM64 completo e assinado, sem root, pelo workflow GitHub Actions do PGS.',
    steps: [
      'Use o APK completo e assinado PGS v0.0.2 para instalação sem root.',
      'Não instale um pacote Root externo por cima do PGS: assinatura e numeração não são de um release PGS.',
      'Uma versão Root futura do PGS precisará de análise própria de compatibilidade, compilação e teste real em dispositivo.',
    ],
    notes: [
      'PGS Root não foi aprovado para a versão v0.0.2.',
      'A documentação Root original permanece como referência separada, com sua atribuição.',
      'O APK PGS sem root mantém sua assinatura permanente e identificador Android.',
    ],
  },
  accounts: {
    title: 'Perfis de conta',
    summary: 'Alterne entre contas lembradas mantendo configurações e locais separados.',
    where: 'Menu rápido > Trocar conta ou Configurações > Contas e backup > Contas e dados > Contas.',
    steps: [
      'Abra Trocar conta e faça login normalmente uma vez em cada conta para criar seu perfil salvo.',
      'Selecione um perfil para trocar. Movimento e automação param, e o jogo reinicia com a sessão lembrada.',
      'Se a sessão expirou, faça login novamente. Confira a conta e a localização antes de iniciar automações.',
      'Para remover um perfil salvo neste dispositivo, primeiro troque para outro perfil e depois exclua o inativo.',
    ],
    notes: [
      'Perfis têm configurações, última localização, histórico de espera, favoritos e rotas salvas próprios. Perfis novos começam com padrões.',
      'Excluir um perfil remove login e dados locais, não a conta do jogo.',
      'Sessões salvas ficam criptografadas no dispositivo e não são exportadas em backups; senhas não são salvas.',
      'Se opções de login sumirem enquanto desconectado, Contas > Redefinir opções de login reinicia o jogo e solicita novamente a data de nascimento.',
      'A autenticação LivePokeMap é compartilhada, mas filtros são separados por perfil.',
      'A troca de contas Root ainda não foi validada para um release PGS.',
    ],
  },
};
