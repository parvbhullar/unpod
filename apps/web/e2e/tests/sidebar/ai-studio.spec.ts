import { test, expect } from '../../fixtures/base.fixture';

test.describe('AI Studio', () => {
  test.skip(
    !process.env.E2E_TEST_USER_EMAIL || !process.env.E2E_TEST_USER_PASSWORD,
    'Skipping AI Studio tests - credentials not configured'
  );

  test('should load AI Studio', async ({ page }) => {
    await page.goto('/ai-studio/');
    await page.waitForLoadState('networkidle');

    await expect(page).toHaveURL(/\/ai-studio/);
    await expect(page.locator('h1, h2')).toBeVisible();
  });
});
