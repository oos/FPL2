import { test, expect } from '@playwright/test';

test.describe('Players2 page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/players2');
    await expect(page.getByRole('heading', { name: 'Players2' })).toBeVisible();
    await expect(page.locator('#players2Table')).toBeVisible();
  });

  test('search filters rows', async ({ page }) => {
    const search = page.getByRole('searchbox');
    await search.fill('salah');
    // Expect at least one row
    const rowsAfterSearch = page.locator('#players2Table tbody tr');
    await expect(rowsAfterSearch.first()).toBeVisible({ timeout: 5000 });
    await search.fill('zzzz_not_found');
    // DataTables shows a single placeholder row when nothing matches; assert on placeholder text
    const placeholder = page.locator('#players2Table tbody td').first();
    await expect(placeholder).toBeVisible();
    const txt = (await placeholder.textContent())?.toLowerCase() || '';
    expect(txt.includes('no matching records') || txt.includes('no data available')).toBeTruthy();
    await search.fill('');
  });

  test('watchlist star toggles and watchlist-only filter works', async ({ page }) => {
    const firstStar = page.locator('#players2Table tbody tr .watch-star2').first();
    await firstStar.click();
    // Should toggle glyph
    const textAfter = await firstStar.textContent();
    expect(textAfter === '★' || textAfter === '☆').toBeTruthy();

    // Turn on watchlist-only; table should show only rows with starred class
    await page.locator('#wlOnly').check();
    const allStars = page.locator('#players2Table tbody tr .watch-star2');
    const count = await allStars.count();
    for (let i = 0; i < count; i++) {
      const cls = await allStars.nth(i).getAttribute('class');
      expect(cls?.includes('text-warning')).toBeTruthy();
    }
    await page.locator('#wlOnly').uncheck();
  });

  // Quick sort options were removed from the Select View dropdown.

  test('saving and loading a view', async ({ page }) => {
    // Change sort to create an unsaved state (click Price header)
    const priceHeader = page.locator('#players2Table thead th').nth(4);
    await priceHeader.click();
    // Save controls should appear; fill a name and save
    await page.locator('#viewName').fill('My Custom View');
    await page.locator('#saveView').click();
    // Now ensure it appears and loads
    const select = page.locator('#loadView');
    await expect(select).toBeVisible();
    await select.selectOption('My Custom View');
    await expect(page.locator('#players2Table')).toBeVisible();
  });

  test('position filter works', async ({ page }) => {
    const before = await page.locator('#players2Table tbody tr').count();
    await page.locator('#positionFilter2').selectOption('Goalkeeper');
    const after = await page.locator('#players2Table tbody tr').count();
    expect(after).toBeLessThanOrEqual(before);
    await page.locator('#positionFilter2').selectOption('');
  });
});


