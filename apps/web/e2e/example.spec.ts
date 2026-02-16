import { test, expect } from '@playwright/test';

/**
 * Quick sanity check tests that run without authentication.
 * These are useful for verifying the basic test setup works.
 */
test.describe('Sanity Checks', () => {
  test('app should be accessible', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Page should load without errors
    await expect(page).toHaveTitle(/.+/);
  });

  test('signin page should load', async ({ page }) => {
    await page.goto('/auth/signin/');
    await page.waitForLoadState('networkidle');

    // Should have form elements
    const emailInput = page
      .locator('input[type="text"], input[type="email"]')
      .first();
    await expect(emailInput).toBeVisible();
  });
});
