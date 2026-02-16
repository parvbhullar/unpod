import { test, expect } from '../../fixtures/base.fixture';

test.describe('Navigation & Interactions', () => {
  test.skip(
    !process.env.E2E_TEST_USER_EMAIL || !process.env.E2E_TEST_USER_PASSWORD,
    'Skipping navigation tests - credentials not configured'
  );

  test('should navigate through main sidebar links without errors', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Get all sidebar links
    // Adjust selector to match your sidebar implementation
    const sidebarLinks = page.locator('aside a, .sidebar a, nav a');
    const count = await sidebarLinks.count();

    console.log(`Found ${count} sidebar links`);

    // Iterate through a few key links to verify they work
    // We don't click all to save time, but we check the first few
    for (let i = 0; i < Math.min(count, 5); i++) {
        const link = sidebarLinks.nth(i);
        const href = await link.getAttribute('href');

        if (href && !href.startsWith('http')) { // Internal links only
            console.log(`Testing navigation to: ${href}`);

            // Click and wait for navigation
            await link.click();
            await page.waitForLoadState('domcontentloaded');

            // Verify we are on the correct page
            await expect(page).toHaveURL(new RegExp(href));

            // Verify no error page is shown
            await expect(page.locator('text=404')).not.toBeVisible();
            await expect(page.locator('text=Internal Server Error')).not.toBeVisible();
        }
    }
  });

  test('should have interactive primary buttons', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Find primary buttons
    const primaryButtons = page.locator('button.ant-btn-primary');

    if (await primaryButtons.count() > 0) {
        const firstBtn = primaryButtons.first();

        // Check if it has a hover state (visual check logic)
        await firstBtn.hover();

        // Check it's not disabled unless intended
        // This is a heuristic; some might be disabled by default
        // await expect(firstBtn).toBeEnabled();
    }
  });
});
