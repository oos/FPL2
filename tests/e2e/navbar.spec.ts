import { test, expect } from '@playwright/test';

test.describe('Navbar navigation', () => {
  test('Players dropdown hover reveals submenu and links work', async ({ page }) => {
    await page.goto('/');
    const playersToggle = page.locator('#players2Dropdown');
    await playersToggle.hover();
    const dropdown = page.locator('ul.dropdown-menu');
    await expect(dropdown).toBeVisible();
    await page.getByRole('link', { name: 'Players' }).click();
    await expect(page).toHaveURL(/\/players2$/);
    await page.locator('#players2Table').isVisible();
  });
});


