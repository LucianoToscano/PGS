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

test('production page loads its assets and stays within the viewport', async ({ page }) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('./');
  await expect(page.locator('h1')).toBeVisible();
  await expect(page.locator('a[href="https://github.com/LucianoToscano/PGS/actions/workflows/pgs-v0.0.2-release.yml"]').first()).toBeVisible();
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

test('verified PGS candidate notes accompany the latest download', async ({ page }) => {
  await page.goto('./');
  const releaseNotes = page.locator(
    '.cta__release a[href="https://github.com/LucianoToscano/PGS/actions/workflows/pgs-v0.0.2-release.yml"]'
  );
  await expect(releaseNotes).toHaveCount(1);
  await expect(releaseNotes).toBeVisible();
  // It must not masquerade as the primary "latest release" call to action.
  await expect(releaseNotes).not.toHaveClass(/btn--primary/);
  await expect(page.locator('.cta__badge')).toHaveText('Candidate');
});
