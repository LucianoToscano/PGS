import * as en from './content.en.js';

// Brazilian Portuguese website copy. IDs, URLs, distances and game-facing
// technical identifiers are deliberately inherited from the English source.
export const links = en.links;

export const nav = [
  { href: '#features', label: 'Recursos' },
  { href: '?guide=all', label: 'Guias de recursos' },
  { href: '#cooldown', label: 'Tempo de espera' },
  { href: '#get-started', label: 'Como começar' },
];

export const heroFacts = [
  { term: 'Compatibilidade', detail: 'Android ARM64 e MuMu — um único APK' },
  { term: 'Modo Root', detail: 'Ainda não lançado na linha PGS' },
  { term: 'Licença', detail: 'MIT (código-fonte do PGS)' },
];

const settingTranslations = [
  {
    label: 'Jogar',
    intro: 'As seis páginas de Jogar na tela inicial de Configurações, além do Menu rápido. Use a busca no topo para localizar uma opção diretamente.',
    items: [
      ['Localização e mapa', 'Simulação de localização, Coordenadas e velocidade (0, 9,3, 16 ou 30 km/h), Mapa mundial, joystick relativo à câmera e Caminhada em espera. Toques no mapa do jogo podem caminhar, teleportar ou combinar as duas ações com toque duplo. Inclui Amplificador de aparições (80 m), experimental e sujeito a lentidão em áreas movimentadas; painel e histórico do tempo de espera, que são estimativas locais; Horário local e contador de encontros.'],
      ['Captura', 'Captura rápida pula as telas após capturar. Arremessos permitem Nice, Great, Excellent ou variedade, com Bola curva, Sempre acertar e bônus AR+ experimental. Chance de captura e Bola automática usam a taxa informada pelo servidor e nunca escolhem uma Master Ball. Arremesso automático e Captura no mapa lançam por você; Frutas define até três frutas em ordem de prioridade.'],
      ['Pokémon e transferência', 'Transfira capturas novas abaixo de 90% de IV, com regras para preservar brilhantes, lendários, eventos, fantasias, fundos, XXS, XXL e IV 0%, uma lista personalizada, botão Manter todos e proteção PvP por classificação de liga. Inclui Evoluir antes de transferir, IVs no encontro, detalhes e armazenamento e Evolução em massa em Ferramentas.'],
      ['Go Plus, Poképaradas e itens', 'Go Plus virtual captura Pokémon selvagens próximos usando apenas bolas vermelhas e gira Poképaradas; inicia desativado e para quando o aplicativo fica em segundo plano. VGP+ adiciona regras de bolas, frutas, arremessos, doces e bola automática, captura Pokémon de incenso e gira discos de ginásios próximos. Inclui Giro rápido, Troca de presentes com Mateo nas rotas e limites para transferência de itens.'],
      ['Batalhas', 'Batalha inteligente monta equipes de contra-ataque e troca Pokémon em ginásios e contra a Equipe GO Rocket. Cura inteligente escolhe poções e reviver para reduzir desperdício. Rocket, Ginásios, Reides e Dynamax têm opções de ataque próprias. Ginásios inclui Colocação e alimentação, Batalhar até derrotar e Alimentação remota; Reides inclui Reide automática.'],
      ['Companheiro, ovos e amigos', 'O Motor de emoção do companheiro usa fotos, carinho e frutas respeitando reservas. Ovos podem ser incubados automaticamente só na incubadora infinita, pela menor ou maior distância. Presentes de amigos abre e envia presentes, com adesivos opcionais, e inicia o lote Enviar e abrir presentes.'],
      ['Menu rápido', 'Toque no ícone do menu para Mapa, Caminhar, Caminhada automática, Rotas no jogo, Feeds, Favoritos, Locais populares, Teleportar, Trocar conta, Eventos, Automação, Pesquisas, Ocultar painel e Configurações. O mapa tem busca de lugares, camadas próximas e 14 locais populares, com aviso de tempo de espera antes de teleportar. Feeds mostra avistamentos de LivePokeMap (assinatura separada) ou PoGoCoordinates.'],
    ],
  },
  {
    label: 'Automação',
    intro: 'As páginas de Automação e Eventos. Cada tarefa pontual só é executada quando você a inicia; a maioria também está em Menu rápido > Automação.',
    items: [
      ['Caçador de shundo (experimental)', 'Teleporta para Pokémon com IV 100% e verifica se são brilhantes, mantendo o encontro brilhante até terminar o tempo de espera. Teleportar constantemente aumenta o risco de advertência ou banimento; considere usar uma conta secundária.'],
      ['Escâner de brilhantes (experimental)', 'Verifica Pokémon selvagens em um raio de 80 m sem capturá-los. Cada checagem usa um encontro; velocidade, espécies e limite de encontros em 24 horas são configuráveis. Pausa quando VGP+, Caçador de shundo ou Reide automática está ativo.'],
      ['Reide automática', 'Encontra a reide compatível mais próxima já carregada pelo jogo, desloca-se até ela, aguarda participantes suficientes, luta conforme as opções de ataque e tenta a captura bônus. Nunca utiliza Passe de Reide a Distância.'],
      ['Sessão de incenso diário', 'Caminhada iniciada manualmente por até 15 minutos. Ao detectar um pássaro de Galar carregado, interrompe caminhada e VGP, tenta abrir o encontro e avisa para capturar manualmente. A passagem real do encontro ainda não foi verificada.'],
      ['Alimentação remota de ginásio', 'Executa um lote nos ginásios defendidos por você, gastando Nanab, Razz e Pinap opcional acima das reservas. Parar cancela tarefas ainda não enviadas; os limites do jogo continuam valendo.'],
      ['Enviar e abrir presentes', 'Executa um lote com contagens confirmadas de presentes enviados e abertos e botão Parar. Abrir com bolsa cheia usa, se ativada, a configuração de recompensas do jogo; requisitos e limites diários continuam válidos.'],
      ['Evolução em massa', 'Pré-visualiza Pokémon de uma etiqueta e evolui cada elegível uma vez sem animação; não ativa Ovos da Sorte automaticamente.'],
      ['Pesquisas', 'Em Pesquisa de campo e Menu rápido > Pesquisas. Resgata pesquisas concluídas, apaga as tarefas selecionadas e captura recompensas pendentes sem a tela de encontro.'],
      ['Eventos', 'Em Configurações de eventos e Menu rápido > Eventos. Go Wild de novembro de 2026 adiciona preferências de Safari Ball, inicialmente desativadas, para Pokémon poderosos em VGP+ e Bola automática. O abridor de caixas do Halloween 2026 continua listado para quando houver caixas no mapa.'],
    ],
  },
  {
    label: 'Aplicativo',
    intro: 'Exibição e desempenho, Contas e backup, busca de configurações e controles dos painéis flutuantes.',
    items: [
      ['Busca de configurações', 'Digite parte do nome, descrição ou uma palavra-chave como “gps falso” ou “modo claro” na busca do topo. Toque em um resultado para abrir a página e rolar até a opção.'],
      ['Interface', 'Tema escuro alterna entre modos claro e escuro, inclusive pelo ícone na tela inicial. Escala da interface ajusta inicializador, menu rápido, joystick, temporizador e painéis para 100, 75, 50 ou 25%.'],
      ['Pular animações', 'Ignora animações de evolução, nascimento, nova espécie, fortalecimento, nível, desbloqueio, medalhas e resultados da Equipe GO Rocket. As batalhas só começam após tocar em Batalhar.'],
      ['Uso da bateria', 'Reduza a resolução, limite a taxa a 20 FPS ou diminua a qualidade gráfica para economizar bateria e aquecer menos o celular.'],
      ['Entradas do menu rápido', 'Oculte opções do menu rápido que não usa. Isso só muda a visibilidade, não ativa ou desativa recursos; Configurações permanece visível.'],
      ['Contas e dados', 'Contas alterna entre contas lembradas com configurações próprias. Exportar/importar salva um backup JSON sem tokens, localização nem rotas. Executar log/exportar abre o registro.'],
      ['Reposicionar painéis', 'Arraste temporizador de espera, relógio local, ícone VGP e botão Manter todos para qualquer posição.'],
      ['Ocultar painel', 'No Menu rápido, deixe a tela parecida com o jogo original: oculte todos os botões, status e textos de IV do PGS; toque com três dedos para exibi-los novamente.'],
    ],
  },
];

export const settingGroups = en.settingGroups.map((group, i) => ({
  ...group,
  label: settingTranslations[i].label,
  intro: settingTranslations[i].intro,
  items: group.items.map((item, j) => ({
    ...item,
    name: settingTranslations[i].items[j][0],
    detail: settingTranslations[i].items[j][1],
  })),
}));

const shotTranslations = {
  'world-map': {
    title: 'Mapa mundial',
    caption: 'Mapa mundial do PGS com favoritos, locais populares, rotas, camadas próximas, botões para copiar localização e ações Caminhar até aqui / Teleportar. Dados do mapa © colaboradores do OpenStreetMap.',
  },
  encounter: {
    title: 'Painéis no encontro',
    caption: 'Encontro do Pokémon GO com leitura opcional de PC, nível e IV acima do Pokémon, quantidade de frutas, escudo de transferência e indicador VGP, sobrepostos ao jogo.',
  },
};
export const screenshots = en.screenshots.map(shot => ({ ...shot, ...shotTranslations[shot.id] }));

const stepTranslations = [
  ['Baixar', 'Abra o release do PGS, baixe PGS.v0.0.5.apk e confira SHA256SUMS.txt. Não instale um arquivo de código-fonte ou pacote de prévia.'],
  ['Instalar', 'Abra o APK em um celular Android ARM64 ou no emulador MuMu, autorizando instalações pelo gerenciador de arquivos quando solicitado.'],
  ['Abrir', 'Inicie o Pokémon GO, toque no pequeno ícone do menu e escolha Configurações para acessar todos os controles.'],
];
export const steps = en.steps.map((step, i) => ({ ...step, title: stepTranslations[i][0], body: stepTranslations[i][1] }));

const faqTranslations = [
  ['Em quais dispositivos funciona?', 'O PGS é destinado a celulares Android ARM64 e ao emulador MuMu, sem root. Uma versão PGS Root ainda não foi validada nem publicada.'],
  ['Posso instalar por cima do app da Play Store?', 'A instalação da Play Store usa outro certificado, portanto não pode ser atualizada no local pelo PGS. Apenas uma instalação existente com o certificado permanente PGS pode receber atualizações preservando seus dados.'],
  ['Existe uma versão PGS Root?', 'Ainda não. A versão do PGS é voltada ao APK sem root. O instalador Root de outro projeto não é uma atualização PGS.'],
  ['O LivePokeMap está incluído?', 'Não. Os feeds remotos exigem uma assinatura ativa própria do LivePokeMap, contratada separadamente no serviço.'],
  ['Garante capturas ou evita banimentos?', 'Não. São modificações experimentais do cliente, sem garantia de resultado no servidor. O temporizador de espera é somente uma estimativa local.'],
  ['Funciona em qualquer versão do jogo?', 'As integrações nativas são feitas para uma versão específica do Pokémon GO. Em outra versão, recursos podem ficar indisponíveis. Confira as notas de cada release.'],
];
export const faqs = en.faqs.map((item, i) => ({ q: faqTranslations[i][0], a: faqTranslations[i][1] }));

export const cooldown = {
  ...en.cooldown,
  intro: 'Considere a distância entre sua última ação sensível à localização e a próxima. O tempo já aguardado conta; teleportar sozinho não reinicia o cronômetro. A tabela comunitária chega a duas horas. Agir cedo demais pode fazer Pokémon fugirem ou giros serem recusados. O PGS faz uma estimativa local, não lê uma contagem regressiva do servidor.',
  triggers: [
    'Capturar Pokémon selvagens, inclusive de incenso e módulos atrair',
    'Arremessar ou deixar cair qualquer bola',
    'Dar uma fruta durante o encontro, inclusive em reides',
    'Girar Poképaradas, mesmo após o limite diário',
    'Ações em ginásios dentro do alcance: colocar, batalhar e alimentar',
    'Fuga causada pelo limite de capturas',
    'Captura ou giro automático',
  ],
  safe: [
    'Teleportar, por si só',
    'Abrir um encontro sem usar bola nem fruta',
    'Caminhar ou chocar ovos',
    'Alimentar ginásios remotamente de fora do alcance',
    'Resgatar recompensas de pesquisas ou da semana; capturar recompensas de pesquisas',
    'Presentes, trocas, evoluções, fortalecimento, transferências e fotos',
    'Trocar companheiro e receber doces',
    'Usar itens em Pokémon ou adicionar um segundo ataque carregado',
    'Ativar Incenso, Ovo da Sorte ou Pedaço de Estrela',
    'Apagar itens do inventário',
    'Batalhas PvP e contra treinadores',
    'Colocar módulos atrair',
    'Alterações na loja ou no avatar',
    'Transferências ao Switch, passes gratuitos e photobombs',
    'Acelerar reides somente após acabar a espera anterior, sem arremessar bola nem dar fruta no encontro da reide',
  ],
  chart: en.cooldown.chart,
};
if(settingTranslations.length!==en.settingGroups.length||en.settingGroups.some((g,i)=>g.items.length!==settingTranslations[i].items.length))throw new Error('Portuguese settings catalog misaligned');
if(faqTranslations.length!==en.faqs.length||stepTranslations.length!==en.steps.length)throw new Error('Portuguese FAQ or setup catalog misaligned');
