import { test, expect } from '../../fixtures/base.fixture';

test.describe('Upgrade', () => {
  test.skip(
    !process.env.E2E_TEST_USER_EMAIL || !process.env.E2E_TEST_USER_PASSWORD,
    'Skipping upgrade tests - credentials not configured'
  );

  test('should load upgrade page', async ({ page }) => {
    await page.goto('/upgrade/');
    await page.waitForLoadState('networkidle');

    await expect(page).toHaveURL(/\/upgrade/);
    await expect(page.locator('h1, h2').first()).toBeVisible();
  });
});
