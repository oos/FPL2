import { test, expect } from '@playwright/test';

test.describe('App pages smoke tests', () => {
  test('Dashboard loads', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: /Upcoming Gameweek/i })).toBeVisible();
  });

  test('FDR loads and table initialized', async ({ page }) => {
    await page.goto('/fdr');
    await expect(page.locator('#fdrTableAll')).toBeVisible();
  });

  test('Players (new) loads', async ({ page }) => {
    await page.goto('/players2');
    await expect(page.locator('#players2Table')).toBeVisible();
  });

  test('Players legacy route redirects to new page', async ({ page }) => {
    await page.goto('/players');
    await expect(page).toHaveURL(/\/players2$/);
    await expect(page.locator('#players2Table')).toBeVisible();
  });

  test('Teams list loads', async ({ page }) => {
    await page.goto('/teams');
    await expect(page.locator('#teamsTable')).toBeVisible();
  });

  test('Squad page loads', async ({ page }) => {
    await page.goto('/squad');
    await expect(page.locator('#gwTabs')).toBeVisible();
  });
});


