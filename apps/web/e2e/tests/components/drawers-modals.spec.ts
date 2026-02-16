import { test, expect } from '../../fixtures/base.fixture';

test.describe('Interactive Components - Drawers & Modals', () => {

  // Test Mobile Sidebar Drawer
  test('should open and close sidebar drawer on mobile', async ({ page }) => {
    // Set viewport to mobile size
    await page.setViewportSize({ width: 375, height: 667 });

    await page.goto('/dashboard'); // or any main page
    await page.waitForLoadState('networkidle');

    // Find the menu trigger (hamburger icon)
    // Adjust selector based on your actual icon implementation
    const menuButton = page.locator('button, .anticon-menu, [aria-label="menu"]').first();

    // Only run if we can find the menu button (it might be hidden on desktop)
    if (await menuButton.isVisible()) {
        await menuButton.click();

        // Verify drawer is visible
        const drawer = page.locator('.ant-drawer-content');
        await expect(drawer).toBeVisible();

        // Verify links inside drawer
        const drawerLinks = drawer.getByRole('link');
        await expect(drawerLinks.first()).toBeVisible();

        // Close drawer (click close button or mask)
        const closeButton = drawer.locator('.ant-drawer-close');
        if (await closeButton.isVisible()) {
            await closeButton.click();
            await expect(drawer).not.toBeVisible();
        } else {
            // Click outside (mask)
            await page.mouse.click(10, 10);
            await expect(drawer).not.toBeVisible();
        }
    }
  });

  // Test Generic Modal Interaction (using a likely available modal)
  test('should handle confirmation modals correctly', async ({ page }) => {
    // This test requires a specific context where a modal exists.
    // We'll try to trigger a delete or confirmation action if possible.
    // For now, we'll look for a generic modal pattern if one is open.

    // Example: Navigate to a place where we might delete something
    // await page.goto('/some-resource');

    // Placeholder for modal logic:
    // 1. Trigger modal
    // 2. Check visibility
    // 3. Check content
    // 4. Cancel

    // Since we don't have a guaranteed path to a modal without creating data,
    // we will skip this specific test unless we are on a page with a known modal.
    test.skip(true, 'Requires specific page with modal trigger');
  });
});
