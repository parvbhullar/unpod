import { test, expect } from '../../fixtures/base.fixture';
import { TEST_USERS } from '../../fixtures/test-data';

test.describe('Main Navigation', () => {
  test.beforeEach(async ({ signInPage, page }) => {
    // Sign in before each test
    await signInPage.goto();
    await signInPage.signIn(TEST_USERS.valid.email, TEST_USERS.valid.password);
    await page.waitForURL(/.*\/dashboard/);
  });

  test('should navigate to the Spaces page from the sidebar', async ({ page }) => {
    // Click on the "Spaces" link in the sidebar
    // Note: The selector might need to be adjusted based on the actual component library and structure
    await page.locator('a[href*="/spaces"]').click();

    // Verify that the URL is correct
    await page.waitForURL(/.*\/spaces/);
    await expect(page).toHaveURL(/.*\/spaces/);

    // Optional: Verify that some content on the Spaces page is visible
    // For example, a heading or a specific element
    await expect(page.locator('h2', { hasText: 'Spaces' })).toBeVisible();
  });
});
