import { test, expect } from '../../fixtures/base.fixture';
import { waitForApiResponse } from '../../utils/api.helper';

test.describe('Call Logs Page', () => {
  // Skip all tests in this file if the required environment variables are not set.
  test.skip(
    !process.env.E2E_TEST_USER_EMAIL || !process.env.E2E_TEST_USER_PASSWORD,
    'Skipping Call Logs tests - credentials not configured'
  );

  test.beforeEach(async ({ page }) => {
    // Navigate to the call logs page before each test.
    await page.goto('/call-logs');
    await page.waitForLoadState('networkidle');
  });

  test('should display call logs table and handle refresh and export', async ({ page }) => {
    // Verify that the main title is visible.
    await expect(page.getByRole('heading', { name: /call logs/i })).toBeVisible();

    // --- Refresh Button ---
    const refreshButton = page.getByRole('button', { name: /refresh/i });
    await expect(refreshButton).toBeVisible();

    const refreshPromise = waitForApiResponse(page, '**/metrics/call-logs/**');
    await refreshButton.click();
    await refreshPromise;

    // --- Export Button ---
    const exportButton = page.getByRole('button', { name: /export/i });
    await expect(exportButton).toBeVisible();

    const downloadPromise = page.waitForEvent('download');
    await exportButton.click();
    const download = await downloadPromise;

    // Verify that the download has started.
    expect(download.suggestedFilename()).toContain('call-logs.csv');
  });
});
