import { test, expect } from '@playwright/test';

test('PGS brand links use the PGS repository and Discord', async ({ page }) => {
  await page.goto('./');
  // On mobile, the first navigation link is inside the closed hamburger menu.
  // Check the actual hrefs, not whether the collapsed menu is visible.
  expect(await page.locator('a[href="https://github.com/LucianoToscano/PGS"]').count()).toBeGreaterThan(0);
  expect(await page.locator('a[href="https://discord.gg/SdwU4VnfW"]').count()).toBeGreaterThan(0);
  const githubLinks = await page.locator('a[href*="github.com/"]').evaluateAll(links =>
    links.map(a => a.href)
  );
  expect(githubLinks.every(url => url.startsWith('https://github.com/LucianoToscano/PGS'))).toBeTruthy();
});

test('official PGS originals load as high-resolution PNGs', async ({ page }) => {
  await page.goto('./');
  const marks = page.locator('img.brand__mark');
  await expect(marks).toHaveCount(2);
  for (const mark of await marks.all()) {
    await expect.poll(() => mark.evaluate(img => [img.naturalWidth, img.naturalHeight])).toEqual([4096, 4096]);
    await expect(mark).toHaveAttribute('src', /pgs-shield\.png$/);
  }
  const wordmark = page.locator('img.hero__wordmark');
  await expect.poll(() => wordmark.evaluate(img => [img.naturalWidth, img.naturalHeight])).toEqual([4096, 1704]);
  await expect(wordmark).toHaveAttribute('src', /pgs-wordmark\.png$/);
  await expect(page.locator('link[rel="icon"]')).toHaveAttribute('href', /pgs-shield\.png$/);
});


test('switches to Brazilian Portuguese, persists the choice and preserves guide deep links', async ({ page }) => {
  await page.goto('./');
  await expect(page.locator('html')).toHaveAttribute('lang', 'en');
  await expect(page.getByRole('combobox', { name: 'Website language' })).toHaveValue('en');

  await page.getByRole('combobox', { name: 'Website language' }).selectOption('pt-BR');
  await expect(page).toHaveURL(/lang=pt-BR/);
  await expect(page.locator('html')).toHaveAttribute('lang', 'pt-BR');
  await expect(page.getByRole('heading', { level: 1 })).toContainText('Sessões mais práticas');
  await expect(page.getByRole('link', { name: 'Ver todos os guias de recursos' })).toHaveAttribute('href', /guide=all&lang=pt-BR/);

  await page.reload();
  await expect(page.locator('html')).toHaveAttribute('lang', 'pt-BR');
  await page.goto('./');
  await expect(page.locator('html')).toHaveAttribute('lang', 'pt-BR');

  await page.goto('./?guide=world-map&lang=pt-BR');
  await expect(page.getByRole('heading', { level: 1, name: 'Mapa mundial' })).toBeVisible();
  await expect(page.locator('main').getByText('Abra o Menu rápido e toque em Mapa.')).toBeVisible();

  await page.getByRole('combobox', { name: 'Idioma do site' }).selectOption('en');
  await expect(page).toHaveURL(/\?guide=world-map$/);
  await expect(page.locator('html')).toHaveAttribute('lang', 'en');
  await expect(page.getByRole('heading', { level: 1, name: 'World map' })).toBeVisible();
});

test('Portuguese navigation, guide search, and mobile layout work', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 740 });
  await page.goto('./?guide=all&lang=pt-BR');
  await expect(page.locator('html')).toHaveAttribute('lang', 'pt-BR');
  await expect(page.getByRole('heading', { level: 1, name: 'Guias de recursos' })).toBeVisible();
  const search = page.getByRole('searchbox', { name: 'Buscar guias' });
  await search.fill('evolução');
  await expect(page.locator('.guide-card').first()).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
  const menu = page.getByRole('button', { name: 'Abrir menu' });
  if (await menu.isVisible()) {
    await menu.click();
    await expect(page.getByRole('navigation', { name: 'Navegação principal' })).toBeVisible();
  }
});

test('production page loads its assets and stays within the viewport', async ({ page }) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('./');
  await expect(page.locator('h1')).toBeVisible();
  await expect(page.locator('a[href="https://github.com/LucianoToscano/PGS/releases/latest"]').first()).toBeVisible();
  for (const image of await page.locator('img').all()) {
    await image.scrollIntoViewIfNeeded();
    await expect.poll(() => image.evaluate(img => img.complete && img.naturalWidth > 0)).toBeTruthy();
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
  expect(errors).toEqual([]);
});

test('in-page navigation points to existing content', async ({ page }) => {
  await page.goto('./');
  const missing = await page.locator('a[href^="#"]').evaluateAll(links =>
    links.map(link => link.getAttribute('href')).filter(href => href.length < 2 || !document.getElementById(href.slice(1)))
  );
  expect(missing).toEqual([]);
});

test('defaults to dark and remembers the chosen theme', async ({ page }) => {
  await page.emulateMedia({ colorScheme: 'light' });
  await page.goto('./');
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  await page.getByRole('button', { name: 'Switch to light theme' }).click();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
  await page.reload();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
  await page.getByRole('button', { name: 'Switch to dark theme' }).click();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
});

test('settings guide and screenshot viewer work with the keyboard', async ({ page }) => {
  await page.goto('./');
  const play = page.getByRole('tab', { name: 'Play', exact: true });
  await play.focus();
  await page.keyboard.press('ArrowRight');
  await expect(page.getByRole('tab', { name: 'Automation', exact: true })).toHaveAttribute('aria-selected', 'true');
  await expect(page.getByRole('tabpanel', { name: 'Automation', exact: true })).toBeVisible();
  const shot = page.locator('.shot-btn').first();
  await shot.focus();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).not.toBeVisible();
  await expect(shot).toBeFocused();
});

test('cooldown nav link reveals the section and its estimate table', async ({ page }) => {
  await page.goto('./');
  // The nav link lives behind the hamburger on narrow viewports; open it first.
  const toggle = page.getByRole('button', { name: 'Open menu' });
  if (await toggle.isVisible()) {
    await toggle.click();
  }
  await page.locator('a[href="#cooldown"]').first().click();
  const section = page.locator('#cooldown');
  await expect(section).toBeVisible();
  await expect(section.getByRole('heading', { level: 2 })).toBeVisible();

  const table = section.locator('table.cooldown__table');
  await expect(table.first().getByRole('columnheader', { name: 'Distance (km)' })).toBeVisible();
  await expect(table.first().getByRole('columnheader', { name: /Wait/ })).toBeVisible();
  // Endpoints of the chart confirm the data rendered in order.
  await expect(table.getByRole('rowheader', { name: '1', exact: true })).toBeVisible();
  await expect(table.getByRole('rowheader', { name: '1350+' })).toBeVisible();
  await expect(table.getByRole('cell', { name: '120 min' })).toBeVisible();
});

test('cooldown chart shows every estimate without internal scrolling or competitor links', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 740 });
  await page.goto('./#cooldown');
  const chart = page.locator('.cooldown__chart');
  await expect(chart.locator('tbody tr')).toHaveCount(30);
  const size = await chart.boundingBox();
  expect(size.height).toBeLessThan(650);
  const scrollable = await chart.locator('*').evaluateAll(elements => elements.filter(element => {
    const style = getComputedStyle(element);
    return ((/auto|scroll/.test(style.overflowY) && element.scrollHeight > element.clientHeight + 1)
      || (/auto|scroll/.test(style.overflowX) && element.scrollWidth > element.clientWidth + 1));
  }).length);
  expect(scrollable).toBe(0);
  await expect(page.locator('img[src*="main-menu.png"]')).toHaveCount(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
});

test('cooldown trigger and safe groups expand', async ({ page }) => {
  await page.goto('./');
  const safe = page.locator('.cooldown__group', { hasText: 'Does not start it' });
  await expect(safe.getByText('Teleporting by itself')).toBeHidden();
  await safe.locator('summary').click();
  await expect(safe.getByText('Teleporting by itself')).toBeVisible();
});

test('PGS release notes accompany the latest download', async ({ page }) => {
  await page.goto('./');
  const releaseNotes = page.locator(
    '.cta__release a[href="https://github.com/LucianoToscano/PGS/releases/tag/v0.0.5"]'
  );
  await expect(releaseNotes).toHaveCount(1);
  await expect(releaseNotes).toBeVisible();
  // It must not masquerade as the primary "latest release" call to action.
  await expect(releaseNotes).not.toHaveClass(/btn--primary/);
  await expect(page.locator('.cta__badge')).toHaveText('Stable');
});

test('archived menu image is absent and bundled public assets resolve', async ({ page, request }) => {
  await page.goto('./');
  const base = new URL('./', page.url());
  const missing = await request.get(new URL('images/main-menu.png', base).href);
  // Static hosting may serve its HTML fallback for a missing asset.
  expect(missing.ok() && (missing.headers()['content-type'] || '').startsWith('image/')).toBeFalsy();
  const paths = new Set(['pgs-shield.png', 'pgs-wordmark.png', 'pgs-full.png']);
  for (const path of await page.locator('main img[src], header img[src], footer img[src]').evaluateAll(
    imgs => imgs.map(img => img.getAttribute('src'))
  )) {
    if (path && !/^https?:/.test(path)) paths.add(path);
  }
  for (const path of paths) {
    const response = await request.get(new URL(path, base).href);
    expect(response.ok(), path).toBeTruthy();
    expect(response.headers()['content-type'], path).toMatch(/^image\//);
  }
});
