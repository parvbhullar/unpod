import { test, expect } from '../../fixtures/base.fixture';

test.describe('Shared Content', () => {
  test.skip(
    !process.env.E2E_TEST_USER_EMAIL || !process.env.E2E_TEST_USER_PASSWORD,
    'Skipping shared content tests - credentials not configured'
  );

  test('should load shared items page', async ({ page }) => {
    await page.goto('/shared/');
    await page.waitForLoadState('networkidle');

    await expect(page).toHaveURL(/\/shared/);
    await expect(page.locator('h1, h2')).toBeVisible();
  });
});
