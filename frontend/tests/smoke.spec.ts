import { test, expect } from '@playwright/test';

test('has title', async ({ page }) => {
    await page.goto('http://localhost:3000');

    // Expect a title "to contain" a substring.
    // Using a generic expectation first to verify page load
    await expect(page).toHaveTitle(/Watchout|Bharat Voyager|Create Next App/);
});
