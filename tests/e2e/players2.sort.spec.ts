import { test, expect } from '@playwright/test';

async function getColumnNumbers(page, colIndex: number, rows = 5): Promise<number[]> {
  const values: number[] = [];
  const cells = page.locator(`#players2Table tbody tr td:nth-child(${colIndex})`);
  const count = Math.min(await cells.count(), rows);
  for (let i = 0; i < count; i++) {
    const txt = (await cells.nth(i).innerText()).replace(/[^0-9.\-]/g, '');
    const num = parseFloat(txt || '0');
    values.push(isNaN(num) ? 0 : num);
  }
  return values;
}

test.describe('Players2 column sorting', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/players2');
    await expect(page.locator('#players2Table')).toBeVisible();
  });

  test('clicking Form header sorts by Form desc then asc', async ({ page }) => {
    const formHeader = page.locator('#players2Table thead th').nth(8); // Form column (indexing from 0)
    // Click once => desc by default
    await formHeader.click();
    let nums = await getColumnNumbers(page, 9);
    const sortedDesc = [...nums].sort((a,b)=>b-a);
    expect(nums.join(',')).toBe(sortedDesc.join(','));
    // Click again => asc
    await formHeader.click();
    nums = await getColumnNumbers(page, 9);
    const sortedAsc = [...nums].sort((a,b)=>a-b);
    expect(nums.join(',')).toBe(sortedAsc.join(','));
  });

  test('clicking Points/£ header sorts', async ({ page }) => {
    const ppmHeader = page.locator('#players2Table thead th').nth(6); // Points/£
    await ppmHeader.click();
    const nums = await getColumnNumbers(page, 7);
    const sortedDesc = [...nums].sort((a,b)=>b-a);
    expect(nums.join(',')).toBe(sortedDesc.join(','));
  });
});


