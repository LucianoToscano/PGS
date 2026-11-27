import { featureGuides as englishGuides } from './featureGuides.js';
import { guidesA } from './featureGuides.pt-BR.a.js';
import { guidesB } from './featureGuides.pt-BR.b.js';
import { guidesC } from './featureGuides.pt-BR.c.js';
import { guidesD } from './featureGuides.pt-BR.d.js';
import { locale } from './locale.js';

// IDs are never translated; links and saved/bookmarked guide URLs stay stable.
const portuguese = { ...guidesA, ...guidesB, ...guidesC, ...guidesD };
const categories = {
  Movement: 'Movimento',
  Map: 'Mapa',
  Automation: 'Automação',
  Reference: 'Referência',
  Catching: 'Captura',
  Inventory: 'Inventário',
  Battles: 'Batalhas',
  Interface: 'Interface',
  Feeds: 'Feeds',
  Personalize: 'Personalização',
};

export const featureGuides = locale === 'pt-BR' ? englishGuides.map(guide => {
  const translated = portuguese[guide.id];
  if (!translated) throw new Error('Missing pt-BR guide: ' + guide.id);
  if (!translated.steps || translated.steps.length !== guide.steps.length ||
      !translated.notes || translated.notes.length !== guide.notes.length ||
      !translated.title || !translated.summary || !translated.where ||
      translated.steps.some(step => !step) || translated.notes.some(note => !note)) {
    throw new Error('Incomplete pt-BR guide: ' + guide.id);
  }
  if (!categories[guide.category]) throw new Error('Untranslated category: ' + guide.category);
  return { ...guide, ...translated, category: categories[guide.category] };
}) : englishGuides;

// Validated by CI separately for both locales.
export const guideTranslations = portuguese;
