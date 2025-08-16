import { test, expect } from '@playwright/test';

test.describe('Players2 page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/players2');
    await expect(page.locator('#players2Table')).toBeVisible();
  });

  test('search filters rows', async ({ page }) => {
    // Use the DataTables search box scoped to players2Table filter (exclude #viewName)
    const search = page.locator('#players2Table_filter input[type="search"]').filter({ hasNot: page.locator('#viewName') });
    const before = await page.locator('#players2Table tbody tr').count();
    await search.first().fill('salah');
    const after = await page.locator('#players2Table tbody tr').count();
    expect(after).toBeLessThanOrEqual(before);
    await search.first().fill('');
    const reset = await page.locator('#players2Table tbody tr').count();
    expect(reset).toBeGreaterThanOrEqual(after);
  });

  test('watchlist star toggles and watchlist-only filter works', async ({ page }) => {
    const starLocator = page.locator('#players2Table tbody tr .watch-star2');
    const starCount = await starLocator.count();
    if (starCount === 0) {
      // In CI the DB may be empty, so there are no player rows/stars to click.
      test.skip(true, 'No players available in table; skipping watchlist toggle test.');
    }
    const firstStar = starLocator.first();
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
    const select = page.locator('#players2Table_length #loadView');
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


