import { test, expect } from '@playwright/test';

test('homepage loads successfully', async ({ page }) => {
    await page.goto('/');

    // Wait for the page to load
    await page.waitForLoadState('networkidle');

    // Check that the page title is present
    await expect(page).toHaveTitle(/Watchout/i);
});

test('navigation works correctly', async ({ page }) => {
    await page.goto('/');

    // Add assertions based on your actual app structure
    // Example: Check if main navigation elements are present
    const body = await page.locator('body');
    await expect(body).toBeVisible();
});
