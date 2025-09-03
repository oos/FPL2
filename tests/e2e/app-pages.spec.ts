import { test, expect } from '@playwright/test';

test.describe('App pages smoke tests', () => {
  test('Dashboard loads', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: /Upcoming Gameweek/i })).toBeVisible();
    // Verify FDR color mapping shows different backgrounds for different difficulties
    const badges = page.locator('.fdr-badge');
    await expect(badges.first()).toBeVisible();
    const colors = await badges.evaluateAll(nodes => nodes.map(n => getComputedStyle(n).backgroundColor));
    // Expect at least 2 distinct colors present if fixtures exist
    expect(new Set(colors).size).toBeGreaterThanOrEqual(2);
  });

  test('FDR loads and table initialized', async ({ page }) => {
    await page.goto('/fdr');
    await expect(page.locator('#fdrTableAll')).toBeVisible();
  });

  test('Players (new) loads', async ({ page }) => {
    await page.goto('/players2');
    await expect(page.locator('#players2Table')).toBeVisible();
  });

  test('Players URL serves new page', async ({ page }) => {
    await page.goto('/players');
    await expect(page.locator('#players2Table')).toBeVisible();
  });

  test('Teams list loads', async ({ page }) => {
    await page.goto('/teams');
    await expect(page.locator('#teamsTable')).toBeVisible();
  });

  test('Squad page loads', async ({ page }) => {
    await page.goto('/squad');
    await expect(page.locator('#gwTabs')).toBeVisible();
    // The page should load successfully even with empty data
    // Check that the basic structure is present
    await expect(page.locator('h3').first()).toBeVisible();
    // Verify the page loaded by checking for the main content
    await expect(page.locator('#gwTabs')).toBeVisible();
  });
});


