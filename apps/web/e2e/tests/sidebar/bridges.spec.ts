import { test, expect } from '../../fixtures/base.fixture';

test.describe('Bridges Feature', () => {
  test.skip(
    !process.env.E2E_TEST_USER_EMAIL || !process.env.E2E_TEST_USER_PASSWORD,
    'Skipping bridges tests - credentials not configured'
  );

  test('should navigate to bridges page', async ({ page }) => {
    await page.goto('/bridges/');
    await page.waitForLoadState('networkidle');

    // Verify URL
    await expect(page).toHaveURL(/\/bridges/);

    // Check for main content
    const content = page.locator('h1, h2, .bridges-container');
    await expect(content.first()).toBeVisible();
  });

  test('should display list of bridges', async ({ page }) => {
    await page.goto('/bridges/');
    await page.waitForLoadState('networkidle');

    // Check for list or empty state
    const list = page.locator('.bridge-list, .empty-state');
    await expect(list.first()).toBeVisible();
  });
});
