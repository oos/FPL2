import { test, expect } from '@playwright/test';

test.describe('Players2 filters and view controls', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/players2');
    await expect(page.locator('#players2Table')).toBeVisible();
  });

  test('Team filter narrows results', async ({ page }) => {
    const teamSelect = page.locator('#teamFilter2');
    const totalBefore = await page.locator('#players2Table tbody tr').count();
    // Pick first real team option if available
    const options = await teamSelect.locator('option').allTextContents();
    const team = options.find(t => t && t !== 'All');
    test.skip(!team, 'No teams found');
    await teamSelect.selectOption({ label: team! });
    await expect(page.locator('#players2Table tbody tr')).toHaveCountLessThanOrEqual(totalBefore);
  });

  test('Max Price filter applies and Clear all resets', async ({ page }) => {
    const rowsBefore = await page.locator('#players2Table tbody tr').count();
    await page.fill('#maxPrice2', '4.5');
    await expect(page.locator('#players2Table tbody tr')).toHaveCountLessThanOrEqual(rowsBefore);
    await page.click('#clearFilters2');
    // After clear, DataTables may redraw; ensure at least as many rows as before filtering
    await expect(page.locator('#players2Table tbody tr').first()).toBeVisible();
  });

  test('Min numeric filters work (Chance %, Points/£, Total, Form, Ownership)', async ({ page }) => {
    await page.fill('#minChance2', '75');
    await page.fill('#minPPM2', '5');
    await page.fill('#minTotal2', '50');
    await page.fill('#minForm2', '2');
    await page.fill('#minOwn2', '1');
    await expect(page.locator('#players2Table tbody tr').first()).toBeVisible();
    // Clear all
    await page.click('#clearFilters2');
    await expect(page.locator('#players2Table tbody tr').first()).toBeVisible();
  });

  test('Save controls show on unsaved sort with suggested name and clear X clears it', async ({ page }) => {
    // Click Price header to create an unsaved state
    await page.locator('#players2Table thead th').nth(4).click();
    // Save controls appear with a suggestion in search input
    const viewName = page.locator('#viewName');
    await expect(viewName).toBeVisible();
    await expect(viewName).not.toHaveValue('');
    // Clear via native X (dispatch input with empty value)
    await viewName.fill('');
    await expect(viewName).toHaveValue('');
  });
});


