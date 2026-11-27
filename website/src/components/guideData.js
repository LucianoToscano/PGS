import { asset } from '../assets.js';
export { featureGuides } from '../featureGuides.i18n.js';
import { localHref } from '../locale.js';

// Query routes work on the static GitHub Pages deployment, including reloads.
export const homeHref = localHref(asset(''));
export const indexHref = localHref(`${asset('')}?guide=all`);
export function guideHref(id) {
  return localHref(`${asset('')}?guide=${encodeURIComponent(id)}`);
}
