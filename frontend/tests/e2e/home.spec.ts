import { test, expect } from '@playwright/test';

test('TE6 E2E Scaffold - Homepage Loads', async ({ page }) => {
    // Assuming frontend runs on localhost:3000 during local dev
    // In CI it might test against a preview URL or local build
    await page.goto('http://localhost:3000/');

    // Expect a title "to contain" a substring.
    await expect(page).toHaveTitle(/Watchout/);

    // Check that the AI disclaimer or a main heading is visible
    const heading = page.locator('h1').first();
    await expect(heading).toBeVisible();
});
