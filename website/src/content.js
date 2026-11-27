// Keep English as the canonical catalog. The locale is selected by an
// explicit ?lang=pt-BR URL, a saved preference, or English by default.
import * as en from './content.en.js';
import * as pt from './content.pt-BR.js';
import { locale } from './locale.js';

const content = locale === 'pt-BR' ? pt : en;
export const { links, nav, heroFacts, settingGroups, screenshots, steps, faqs, cooldown } = content;
