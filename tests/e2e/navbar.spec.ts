import { test, expect } from '@playwright/test';

test.describe('Navbar navigation', () => {
  test('Players navigation works', async ({ page }) => {
    await page.goto('/');
    // Wait for the page to be fully loaded
    await page.waitForLoadState('networkidle');
    
    // Test that the Players link exists and can be clicked
    const playersLink = page.locator('a.nav-link').filter({ hasText: 'Players' });
    await expect(playersLink).toBeVisible();
    
    // Test direct navigation to players page
    await page.goto('/players');
    await expect(page).toHaveURL(/\/players$/);
    await page.locator('#players2Table').isVisible();
  });
});


