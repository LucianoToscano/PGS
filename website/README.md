# PGS website — English / Português (Brasil)

The website defaults to English and offers a Brazilian Portuguese selector. This is separate from the 12 in-app language choices.

The public app showcase lives at [lucianotoscano.github.io/PGS](https://lucianotoscano.github.io/PGS/). It is a static React site built with Vite. The Android app and APK release workflows are independent of this site.

## Local development

Use Node 24 and npm:

```sh
cd website
npm ci
npm run dev
```

Open the printed local URL with the `/PGS/` path. To verify the production build:

```sh
npm run build
npx playwright install chromium
npm test
```

The browser checks use the production preview server. Generated output, installed dependencies, and test receipts are ignored.

## Publishing

The `Website` workflow builds and checks pull requests. Changes to `website/` or the workflow on `main` also deploy to GitHub Pages. Repository Pages must use **GitHub Actions** as its source. Only the deployment job receives Pages write and OIDC permissions. It cannot publish APK releases or send release announcements.

The Vite base path is `/PGS/`. Keep image links base-aware when adding screenshots. Download buttons point to `/releases/latest`; the release notes link is pinned to v0.0.5. The project owner confirmed installation and app opening on a physical device. Google sign-in and in-app update remain unverified.

## Feature guides and routing

The site has three views selected by a query string, so the static GitHub Pages deploy needs no client-side router and every link survives reload, sharing, and the back button:

- no query — the marketing homepage (`Hero`, `Features`, `Cooldown`, `GetStarted`).
- `?guide=all` — the feature-guide index (`GuideIndex`): the guides grouped by `category` with a text filter.
- `?guide=<id>` — one guide (`GuideDetail`). An unknown id renders an in-page "Guide not found" with a link back to the index.

`App.jsx` reads `window.location.search` once on load, picks the view, and updates `document.title` and the `meta[name="description"]` to match. Guide links are ordinary `<a>` elements whose `href` changes the query, which triggers a full load of the same `index.html`. On guide views the header/footer logo and nav point back at the homepage and its section anchors (`/PGS/#features`, …) instead of dead in-page fragments.

Guide content lives in `src/featureGuides.js`, which exports `featureGuides` — an array of `{ id, title, category, summary, where, steps[], notes[] }`. That file is maintained separately from the layout. `src/components/guideData.js` re-exports the catalog and provides base-aware links. To add or edit a guide, update `featureGuides.js`; the index and detail pages pick it up without component edits. The homepage Features section links to the guide index.

Release-specific availability and validation details belong in the release notes.

## Screenshots and artwork

- `public/pgs-shield.png`: original 4096 × 4096 transparent PGS shield from Google Drive; used by the header, footer and favicon.
- `public/pgs-full.png`: original 4096 × 4096 complete official PGS logo; used by the repository README and social preview.
- `public/pgs-wordmark.png`: original 4096 × 1704 horizontal PGS logo; used by the website hero.
- Each PNG is byte-for-byte identical to the Drive original. The PGS branding source copies are stored in `pgs/branding/`. The in-game menu icon is intentionally preserved independently for Android compatibility.
- The outdated menu screenshot was removed because it showed another project's branding and did not represent the current PGS interface. Never present historical captures as verified current releases.
- `public/images/encounter.png`: real encounter capture showing the IV/level, transfer and berry overlays.
- `public/images/world-map.png`: November 2026 MuMu capture of the app's world map (v0.3.5 interface). OpenStreetMap attribution is visible in the capture.

Screenshots are representative; enabled options and layout depend on your settings and build. Do not publish account names, email addresses, tokens, or private locations in new captures. Game artwork is not covered by the source MIT license; see the repository's [third-party notices](../THIRD_PARTY.md). Map data is © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright).

## Cooldown guidance

The Cooldown section uses original text and two compact tables with all 30 estimates visible without internal scrolling. The values are guidance, not a published server contract. The app interpolates between distances and rounds up to whole minutes. Preserve the chart values and action exceptions when adjusting presentation. Published release downloads remain separate from development-build guides.

## Guide screenshots

Feature pages use `src/guideScreenshots.js` and the shared `Gallery` component. The 13 WebP images under `public/images/guides/` are archived research captures, not evidence of the current PGS release, cropped to the relevant panel: hotspots, hotspot actions, teleport cooldown and event boxes from the experimental.3 APK on 2026-10-31 (those screens did not change in the redesign), and the rest from the v0.3.5 interface on 2026-11-18, including settings search and Mateo gift exchange. No controls or results were synthesized. Captions identify example settings rather than defaults or proof of successful gameplay; the map example selects Pier 39 without moving the character. OpenStreetMap attribution remains visible.

Keep captures free of account names, saved places, private coordinates and unrelated overlays. Original captures and crop receipts remain in local diagnostic artifacts; publish only the reviewed panel images. The image catalog records dimensions for stable layout. Guide galleries support keyboard opening, Escape, a close button and focus restoration.

## Website localization (EN / PT-BR)

The site defaults to **English**. The language selector in the header supports **EN** and **PT-BR** on desktop and mobile. Brazilian Portuguese adds a stable `?lang=pt-BR` parameter to links, including deep links such as `?guide=world-map&lang=pt-BR`. The choice is also saved in `pgs-website-language`. Switching language preserves the current guide and does not affect the theme or in-game language.

- `src/locale.js` owns the language selection, URL handling and persistence.
- `src/uiText.js` translates site chrome and accessibility labels.
- `src/content.en.js` is the canonical English homepage/settings text.
- `src/content.pt-BR.js` is its Brazilian Portuguese counterpart; `src/content.js` selects one.
- `src/featureGuides.js` is the canonical English guide catalog. The four `src/featureGuides.pt-BR.*.js` translation catalogs preserve all 37 guide IDs and step/note counts; `src/featureGuides.i18n.js` selects one.
- `src/guideScreenshots.i18n.js` translates guide screenshot titles and captions without changing source images or dimensions.

Update English and Brazilian Portuguese catalogs **in the same pull request** for any user-visible change. Do not translate the URL guide slugs, technical identifiers, checksum values, APK names or saved Android preferences. `npm test` checks both languages, direct links and content parity.

Historical screenshots illustrate the controls only; they are not proof of the current release. The obsolete full-menu screenshot is deliberately absent. Replacements require a current, privacy-reviewed device capture.
