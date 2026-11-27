import { guideScreenshots as english } from './guideScreenshots.js';
import { locale } from './locale.js';

const translations = {
  'vgp-plus': [
    'Configurações VGP+',
    'Go Plus virtual na página Go Plus, Poképaradas e itens: alvos próximos, pausa estimada, Bola automática, opções de bola e fruta, limites de PC e nível, qualidade do arremesso, variedade e bola curva. Inicie ou pare no painel VGP.',
  ],
  'buddy-emotion': [
    'Cuidados do companheiro',
    'Motor de emoção em Companheiro, ovos e amigos, com ordem de frutas, reservas, abertura opcional de presentes e painel EP. A conta desta captura não tinha companheiro escolhido, então o status solicita um; não há garantia de tempo até a empolgação.',
  ],
  'buddy-priority': [
    'Ordem de frutas',
    'As frutas numeradas definem a ordem de alimentação: Nanab, Frambo e depois Caxí neste exemplo. Frutas premium estão desmarcadas. Salvar confirma; Cancelar mantém a escolha anterior.',
  ],
  'batch-evolution': [
    'Prévia de evolução em massa',
    'Prévia antes de evoluir: informe a etiqueta Evolve e, opcionalmente, ative remoção da etiqueta. Iniciar permanece desabilitado até que exista um lote elegível pré-visualizado. Nenhuma evolução foi iniciada nesta captura.',
  ],
  battles: [
    'Opções de automação em batalhas',
    'Página de Batalhas: Ginásios, Reides e Dynamax têm opções próprias de ataque rápido, ataque carregado e esquiva, junto de Colocação e alimentação, Batalhar até ser derrotado, Alimentação remota e Reide automática. Ataque rápido ou carregado de ginásio também inicia a luta contra o próximo adversário.',
  ],
  'gym-slotter': [
    'Colocação e alimentação de ginásio',
    'As ações de colocação e alimentação estão selecionadas, mas Executar está desligado. Alternativa e reservas de frutas mostradas são preferências de exemplo, não os valores padrão.',
  ],
  'event-boxes': [
    'Coleta de caixas de Halloween',
    'A opção de Halloween abre caixas visíveis e pula encontros sem capturar. Não seleciona apenas caixas de doces.',
  ],
  hotspots: [
    'Selecionar local popular',
    'Lista de locais populares do Menu rápido. Os fusos UTC exibidos são valores de referência e podem variar conforme a estação do ano.',
  ],
  'hotspot-actions': [
    'Caminhar ou teleportar',
    'Selecionar Pier 39 no Menu rápido oferece Caminhar e Teleportar. Teleportar abre confirmação separada de espera.',
  ],
  'teleport-cooldown': [
    'Conferir espera do destino',
    'Confirmação de tempo de espera para Pier 39. Zero é a estimativa desta captura; ações anteriores e tempo decorrido determinam a estimativa. O teleporte foi cancelado.',
  ],
  'world-map': [
    'Selecionar destino no mapa',
    'Pier 39 aparece como destino vermelho, com busca, locais populares, camadas e botões para copiar localização. Selecionar não move o personagem; Caminhar até aqui ou Teleportar são ações separadas. Dados: colaboradores do OpenStreetMap.',
  ],
  'settings-search': [
    'Buscar configurações',
    'Buscar “auto ball” mostra sete configurações correspondentes, com grupo e página. Tocar em um resultado abre a página nessa opção.',
  ],
  'mateo-gift-exchange': [
    'Trocar presentes com Mateo',
    'A opção de troca com Mateo fica no grupo Rotas de Go Plus, Poképaradas e itens. É salva por conta e começa desligada.',
  ],
};

export const guideScreenshots = locale === 'pt-BR'
  ? Object.fromEntries(Object.entries(english).map(([guide, shots]) => [
      guide,
      shots.map(shot => {
        const translated = translations[shot.id];
        if (!translated) throw new Error('Missing screenshot translation: ' + shot.id);
        return { ...shot, title: translated[0], caption: translated[1] };
      }),
    ]))
  : english;
