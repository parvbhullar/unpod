import { test, expect } from '../../fixtures/base.fixture';

test.describe('Settings', () => {
  test.skip(
    !process.env.E2E_TEST_USER_EMAIL || !process.env.E2E_TEST_USER_PASSWORD,
    'Skipping settings tests - credentials not configured'
  );

  test('should allow changing application language', async ({ page }) => {
    await page.goto('/settings/');
    await page.waitForLoadState('networkidle');

    // Look for a language selector (usually a select dropdown)
    const languageSelect = page.locator('.ant-select').filter({ hasText: /language|english/i });

    if (await languageSelect.isVisible()) {
        await languageSelect.click();

        // Select a different language (e.g., Spanish or just the second option)
        const options = page.locator('.ant-select-item-option');
        if (await options.count() > 1) {
            const optionToSelect = options.nth(1);
            const optionText = await optionToSelect.textContent();

            await optionToSelect.click();

            // Verify the selection updated
            await expect(languageSelect).toContainText(optionText || '');

            // Save if there's a save button
            const saveButton = page.getByRole('button', { name: /save|update/i });
            if (await saveButton.isVisible()) {
                await saveButton.click();
                await expect(page.locator('.ant-message-success, .toast-success')).toBeVisible();
            }
        }
    }
  });

  test('should allow toggling notification preferences', async ({ page }) => {
    await page.goto('/settings/');
    await page.waitForLoadState('networkidle');

    // Look for a switch/toggle
    const toggle = page.locator('.ant-switch').first();

    if (await toggle.isVisible()) {
        const initialState = await toggle.getAttribute('aria-checked');

        // Click to toggle
        await toggle.click();

        // Verify state changed
        const expectedState = initialState === 'true' ? 'false' : 'true';
        await expect(toggle).toHaveAttribute('aria-checked', expectedState);

        // Save if needed
        const saveButton = page.getByRole('button', { name: /save|update/i });
        if (await saveButton.isVisible()) {
            await saveButton.click();
            await expect(page.locator('.ant-message-success, .toast-success')).toBeVisible();
        }
    }
  });
});
