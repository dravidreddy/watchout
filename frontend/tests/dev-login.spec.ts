import { test, expect } from '@playwright/test';

test('dev login flow', async ({ page }) => {
    // 1. Go to Login Page
    await page.goto('http://localhost:3000');

    // Wait for loading to finish
    try {
        const loader = page.getByText('Loading...');
        if (await loader.isVisible()) {
            await loader.waitFor({ state: 'hidden', timeout: 5000 });
        }
    } catch (e) {
        // Ignore timeout if loader wasn't there
    }

    // 2. Check for Dev Login Button
    const devButton = page.getByRole('button', { name: 'Dev/QA Login' });
    await expect(devButton).toBeVisible();

    // 3. Click to Login
    await devButton.click();

    // 4. Verify Redirect (Successful login should move away from login page)
    await expect(page).not.toHaveURL('http://localhost:3000');
});
