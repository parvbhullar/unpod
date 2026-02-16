import { test, expect } from '../../fixtures/base.fixture';

test.describe('Wallet Page', () => {
  // Skip all tests in this file if the required environment variables are not set.
  test.skip(
    !process.env.E2E_TEST_USER_EMAIL || !process.env.E2E_TEST_USER_PASSWORD,
    'Skipping Wallet tests - credentials not configured'
  );

  test.beforeEach(async ({ page }) => {
    // Navigate to the wallet page before each test.
    await page.goto('/wallet');
    await page.waitForLoadState('networkidle');
  });

  test('should display wallet balance, transaction history, and allow adding credits', async ({ page }) => {
    // Verify that the wallet balance is visible.
    await expect(page.getByText(/credits/i)).toBeVisible();

    // Verify that the transaction history table is visible.
    await expect(page.getByText('Transaction ID')).toBeVisible();
    await expect(page.getByText('Amount')).toBeVisible();
    await expect(page.getByText('Date')).toBeVisible();
    await expect(page.getByText('Status')).toBeVisible();

    // --- Add Credits ---
    const addButton = page.getByRole('button', { name: /add/i });
    await expect(addButton).toBeVisible();
    await addButton.click();

    // The "Add" button opens a drawer with a form.
    const drawer = page.locator('.ant-drawer-content');
    await expect(drawer).toBeVisible();

    // Fill out the form.
    await drawer.getByLabel(/amount/i).fill('10');

    // Click the "Add Credits" button.
    const addCreditsButton = drawer.getByRole('button', { name: /add credits/i });
    await addCreditsButton.click();

    // The application will redirect to a payment gateway.
    // For this test, we will just verify that the drawer closes.
    await expect(drawer).not.toBeVisible();
  });
});
