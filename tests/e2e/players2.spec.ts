import { test, expect } from '@playwright/test';

test.describe('Players2 page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/players2');
    // Wait for the table to be visible and loaded
    await expect(page.locator('#players2Table')).toBeVisible();
    // Wait for data to load
    await page.waitForSelector('#players2Table tbody tr', { timeout: 10000 });
  });

  test('search filters rows', async ({ page }) => {
    // Wait for table to be fully loaded
    await page.waitForSelector('#players2Table tbody tr', { timeout: 10000 });
    
    // Get initial row count
    const before = await page.locator('#players2Table tbody tr').count();
    expect(before).toBeGreaterThan(0);
    
    // Find the search input (exclude viewName input)
    const searchInput = page.locator('#players2Table_filter input[type="search"]').first();
    await expect(searchInput).toBeVisible();
    
    // Perform search
    await searchInput.fill('salah');
    await page.waitForTimeout(500); // Wait for search to complete
    
    const after = await page.locator('#players2Table tbody tr').count();
    expect(after).toBeLessThanOrEqual(before);
    
    // Clear search
    await searchInput.clear();
    await page.waitForTimeout(500);
    
    const reset = await page.locator('#players2Table tbody tr').count();
    expect(reset).toBeGreaterThanOrEqual(after);
  });

  test('watchlist star toggles and watchlist-only filter works', async ({ page }) => {
    // Wait for table to be fully loaded
    await page.waitForSelector('#players2Table tbody tr', { timeout: 10000 });
    
    const starLocator = page.locator('#players2Table tbody tr .watch-star2');
    const starCount = await starLocator.count();
    
    if (starCount === 0) {
      // In CI the DB may be empty, so there are no player rows/stars to click.
      test.skip(true, 'No players available in table; skipping watchlist toggle test.');
    }
    
    const firstStar = starLocator.first();
    await expect(firstStar).toBeVisible();
    
    // Get initial state
    const initialText = await firstStar.textContent();
    
    // Click the star
    await firstStar.click();
    await page.waitForTimeout(500);
    
    // Should toggle glyph
    const textAfter = await firstStar.textContent();
    expect(textAfter === '★' || textAfter === '☆').toBeTruthy();
    expect(textAfter).not.toBe(initialText);

    // Turn on watchlist-only filter
    const wlOnlyCheckbox = page.locator('#wlOnly');
    await expect(wlOnlyCheckbox).toBeVisible();
    await wlOnlyCheckbox.check();
    await page.waitForTimeout(500);
    
    // Table should show only rows with starred class
    const allStars = page.locator('#players2Table tbody tr .watch-star2');
    const count = await allStars.count();
    
    for (let i = 0; i < count; i++) {
      const cls = await allStars.nth(i).getAttribute('class');
      expect(cls?.includes('text-warning')).toBeTruthy();
    }
    
    // Uncheck filter
    await wlOnlyCheckbox.uncheck();
    await page.waitForTimeout(500);
  });

  test('saving and loading a view', async ({ page }) => {
    // Wait for table to be fully loaded
    await page.waitForSelector('#players2Table tbody tr', { timeout: 10000 });
    
    // Change sort to create an unsaved state (click Price header)
    const priceHeader = page.locator('#players2Table thead th').nth(4);
    await expect(priceHeader).toBeVisible();
    await priceHeader.click();
    await page.waitForTimeout(500);
    
    // Save controls should appear; fill a name and save
    const viewNameInput = page.locator('#viewName');
    await expect(viewNameInput).toBeVisible();
    await viewNameInput.fill('My Custom View');
    
    const saveButton = page.locator('#saveView');
    await expect(saveButton).toBeVisible();
    await saveButton.click();
    await page.waitForTimeout(500);
    
    // Now ensure it appears and loads
    const select = page.locator('#players2Table_length #loadView');
    await expect(select).toBeVisible();
    await select.selectOption('My Custom View');
    await page.waitForTimeout(500);
    
    await expect(page.locator('#players2Table')).toBeVisible();
  });

  test('position filter works', async ({ page }) => {
    // Wait for table to be fully loaded
    await page.waitForSelector('#players2Table tbody tr', { timeout: 10000 });
    
    const before = await page.locator('#players2Table tbody tr').count();
    expect(before).toBeGreaterThan(0);
    
    const positionFilter = page.locator('#positionFilter2');
    await expect(positionFilter).toBeVisible();
    await positionFilter.selectOption('Goalkeeper');
    await page.waitForTimeout(500);
    
    const after = await page.locator('#players2Table tbody tr').count();
    expect(after).toBeLessThanOrEqual(before);
    
    // Reset filter
    await positionFilter.selectOption('');
    await page.waitForTimeout(500);
  });

  test('team filter works', async ({ page }) => {
    // Wait for table to be fully loaded
    await page.waitForSelector('#players2Table tbody tr', { timeout: 10000 });
    
    const before = await page.locator('#players2Table tbody tr').count();
    expect(before).toBeGreaterThan(0);
    
    const teamFilter = page.locator('#teamFilter2');
    await expect(teamFilter).toBeVisible();
    
    // Select a team (assuming Liverpool exists)
    await teamFilter.selectOption('Liverpool');
    await page.waitForTimeout(500);
    
    const after = await page.locator('#players2Table tbody tr').count();
    expect(after).toBeLessThanOrEqual(before);
    
    // Reset filter
    await teamFilter.selectOption('');
    await page.waitForTimeout(500);
  });

  test('clear all filters resets view', async ({ page }) => {
    // Wait for table to be fully loaded
    await page.waitForSelector('#players2Table tbody tr', { timeout: 10000 });
    
    const initialCount = await page.locator('#players2Table tbody tr').count();
    
    // Apply some filters
    const positionFilter = page.locator('#positionFilter2');
    await positionFilter.selectOption('Midfielder');
    await page.waitForTimeout(500);
    
    const filteredCount = await page.locator('#players2Table tbody tr').count();
    expect(filteredCount).toBeLessThanOrEqual(initialCount);
    
    // Clear all filters
    const clearButton = page.locator('#clearAllFilters');
    if (await clearButton.isVisible()) {
      await clearButton.click();
      await page.waitForTimeout(500);
      
      const clearedCount = await page.locator('#players2Table tbody tr').count();
      expect(clearedCount).toBe(initialCount);
    }
  });

  test('sorting works correctly', async ({ page }) => {
    // Wait for table to be fully loaded
    await page.waitForSelector('#players2Table tbody tr', { timeout: 10000 });
    
    // Test sorting by different columns
    const sortableHeaders = ['#', 'Name', 'Team', 'Position', 'Price', 'Points', 'Form', 'Ownership'];
    
    for (let i = 0; i < sortableHeaders.length; i++) {
      const header = page.locator('#players2Table thead th').nth(i);
      if (await header.isVisible()) {
        await header.click();
        await page.waitForTimeout(500);
        
        // Verify sorting indicator appears
        const hasSortClass = await header.evaluate(el => 
          el.classList.contains('sorting_asc') || 
          el.classList.contains('sorting_desc')
        );
        expect(hasSortClass).toBeTruthy();
      }
    }
  });

  test('pagination works', async ({ page }) => {
    // Wait for table to be fully loaded
    await page.waitForSelector('#players2Table tbody tr', { timeout: 10000 });
    
    const paginationInfo = page.locator('#players2Table_info');
    if (await paginationInfo.isVisible()) {
      const infoText = await paginationInfo.textContent();
      expect(infoText).toContain('Showing');
      
      // Test next page if available
      const nextButton = page.locator('#players2Table_next');
      if (await nextButton.isVisible()) {
        const isDisabled = await nextButton.evaluate(el => el.classList.contains('disabled'));
        if (!isDisabled) {
          await nextButton.click();
          await page.waitForTimeout(500);
          
          // Verify page changed
          const newInfoText = await paginationInfo.textContent();
          expect(newInfoText).not.toBe(infoText);
        }
      }
    }
  });

  test('table responsiveness', async ({ page }) => {
    // Test on different viewport sizes
    const viewports = [
      { width: 1920, height: 1080 },
      { width: 1366, height: 768 },
      { width: 768, height: 1024 },
      { width: 375, height: 667 }
    ];
    
    for (const viewport of viewports) {
      await page.setViewportSize(viewport);
      await page.waitForTimeout(500);
      
      // Table should still be visible and functional
      await expect(page.locator('#players2Table')).toBeVisible();
      
      // Check if table has horizontal scroll on small screens
      if (viewport.width < 768) {
        const tableWrapper = page.locator('#players2Table_wrapper');
        const hasScroll = await tableWrapper.evaluate(el => 
          el.scrollWidth > el.clientWidth
        );
        // Table should be scrollable on small screens
        expect(hasScroll).toBeTruthy();
      }
    }
  });
});


