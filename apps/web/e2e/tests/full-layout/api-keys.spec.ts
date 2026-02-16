import { test, expect } from '../../fixtures/base.fixture';
import { waitForApiResponse } from '../../utils/api.helper';

test.describe('API Keys Page', () => {
  // Skip all tests in this file if the required environment variables are not set.
  test.skip(
    !process.env.E2E_TEST_USER_EMAIL || !process.env.E2E_TEST_USER_PASSWORD,
    'Skipping API Keys tests - credentials not configured'
  );

  test.beforeEach(async ({ page }) => {
    // Navigate to the API keys page before each test.
    await page.goto('/api-keys');
    await page.waitForLoadState('networkidle');
  });

  test('should generate and delete an API key', async ({ page }) => {
    // --- Generate Key ---
    const generateButton = page.getByRole('button', { name: /generate new/i });
    await expect(generateButton).toBeVisible();

    // If the button is disabled, it means a key already exists.
    // We need to delete it first to enable the generate button.
    if (await generateButton.isDisabled()) {
      const deleteButton = page.getByRole('button', { name: /delete/i }).first();
      await deleteButton.click();
      // Confirm the deletion in the popover.
      await page.getByRole('button', { name: 'OK' }).click();
      await page.waitForResponse('**/user/auth-tokens/**');
    }

    // Now, click the "Generate New" button.
    await generateButton.click();

    // Wait for the API call to complete and assert that a success message is shown.
    await waitForApiResponse(page, '**/user/auth-tokens/');
    await expect(page.locator('.ant-message-success')).toBeVisible();

    // Verify that the new key appears in the table.
    const table = page.locator('.ant-table-tbody');
    await expect(table.locator('tr')).toHaveCount(1);

    // --- Delete Key ---
    const deleteButton = page.getByRole('button', { name: /delete/i }).first();
    await expect(deleteButton).toBeVisible();
    await deleteButton.click();

    // Confirm the deletion in the popover.
    await page.getByRole('button', { name: 'OK' }).click();

    // Wait for the API call to complete and assert that a success message is shown.
    await waitForApiResponse(page, '**/user/auth-tokens/**');
    await expect(page.locator('.ant-message-success')).toBeVisible();

    // Verify that the table is now empty.
    await expect(table.locator('tr')).toHaveCount(0);
  });
});
