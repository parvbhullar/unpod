import { test, expect } from '../../fixtures/base.fixture';

test.describe('Billing Page', () => {
  // Skip all tests in this file if the required environment variables are not set.
  test.skip(
    !process.env.E2E_TEST_USER_EMAIL || !process.env.E2E_TEST_USER_PASSWORD,
    'Skipping Billing tests - credentials not configured'
  );

  test.beforeEach(async ({ page }) => {
    // Navigate to the billing page before each test.
    await page.goto('/billing');
    await page.waitForLoadState('networkidle');
  });

  test('should display billing details and navigate to upgrade page', async ({ page }) => {
    // Verify that the main title is visible.
    await expect(page.getByRole('heading', { name: /billing/i })).toBeVisible();

    // Verify that the active plan summary is visible.
    await expect(page.getByText(/active plan/i)).toBeVisible();

    // Verify that the monthly usage report is visible.
    await expect(page.getByText(/monthly usage report/i)).toBeVisible();

    // Verify that the payment statements section is visible.
    await expect(page.getByText(/payment statements/i)).toBeVisible();

    // Find the "Upgrade" or "Choose Plan" button and click it.
    const upgradeButton = page.getByRole('button', { name: /upgrade|choose plan/i });
    await expect(upgradeButton).toBeVisible();
    await upgradeButton.click();

    // Verify that the URL has changed to the upgrade page.
    await page.waitForURL('**/billing/upgrade');
    expect(page.url()).toContain('/billing/upgrade');
  });
});
