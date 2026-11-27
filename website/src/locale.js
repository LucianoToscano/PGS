export const LOCALES = Object.freeze(['en', 'pt-BR']);
const STORAGE_KEY = 'pgs-website-language';

function savedLanguage() {
  try {
    return window.localStorage.getItem(STORAGE_KEY);
  } catch (_error) {
    return null;
  }
}

export function readLocale() {
  if (typeof window === 'undefined') return 'en';
  const params = new URLSearchParams(window.location.search);
  const fromUrl = params.get('lang');
  if (LOCALES.includes(fromUrl)) return fromUrl;
  const saved = savedLanguage();
  return LOCALES.includes(saved) ? saved : 'en';
}

export const locale = readLocale();

// For a link to the same site, preserve the selected locale. English remains
// the clean, canonical URL. Shared ?guide=...&lang=pt-BR links are permanent.
export function localHref(href, language = locale) {
  if (language !== 'pt-BR') return href;
  const [withoutHash, fragment] = String(href).split('#');
  const suffix = withoutHash.includes('?') ? '&' : '?';
  return withoutHash + suffix + 'lang=pt-BR' + (fragment === undefined ? '' : '#' + fragment);
}

export function selectLocale(next) {
  if (!LOCALES.includes(next) || typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(STORAGE_KEY, next);
  } catch (_error) {
    // The explicit URL works even if browser storage is unavailable.
  }
  const url = new URL(window.location.href);
  if (next === 'en') url.searchParams.delete('lang');
  else url.searchParams.set('lang', next);
  window.location.assign(url.href);
}
