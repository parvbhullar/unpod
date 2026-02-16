import { test, expect } from '../../fixtures/base.fixture';

test.describe('Interactive Components - Tabs & Selects', () => {
  test.skip(
    !process.env.E2E_TEST_USER_EMAIL || !process.env.E2E_TEST_USER_PASSWORD,
    'Skipping component tests - credentials not configured'
  );

  test('should switch tabs correctly', async ({ page }) => {
    // We'll use the AI Studio Agent Configuration page as it has a robust tab system
    // First, we need to navigate to an agent or create a new one context
    // For simplicity, we'll go to the 'new' page which has tabs
    await page.goto('/ai-studio/new');
    await page.waitForLoadState('networkidle');

    // Locate tabs
    // Ant Design tabs usually have role="tab"
    const tabs = page.getByRole('tab');

    // Check if we have multiple tabs
    if (await tabs.count() > 1) {
        const firstTab = tabs.nth(0);
        const secondTab = tabs.nth(1);

        // Click second tab
        await secondTab.click();

        // Verify it becomes active
        await expect(secondTab).toHaveAttribute('aria-selected', 'true');
        await expect(firstTab).toHaveAttribute('aria-selected', 'false');

        // Verify content change (heuristic: check if a unique form field for that tab appears)
        // This depends on the specific tab content, but generally the URL might not change for simple tabs,
        // but the visible content will.
    }
  });

  test('should handle select dropdowns correctly', async ({ page }) => {
    await page.goto('/ai-studio/new');
    await page.waitForLoadState('networkidle');

    // Find a select component (Ant Design select)
    // We look for the trigger div
    const selectTrigger = page.locator('.ant-select-selector').first();

    if (await selectTrigger.isVisible()) {
        // Click to open dropdown
        await selectTrigger.click();

        // Wait for dropdown options to appear
        // Ant Design renders options in a portal at the root level usually
        const options = page.locator('.ant-select-item-option');
        await expect(options.first()).toBeVisible();

        // Select the first available option
        const firstOption = options.first();
        const optionText = await firstOption.textContent();

        await firstOption.click();

        // Verify the select now shows the chosen option
        await expect(selectTrigger).toContainText(optionText || '');
    }
  });
});
