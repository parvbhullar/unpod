import { test, expect } from '../fixtures/base.fixture';
import { openAndVerifyDrawer } from '../utils/ui.helper';

test.describe('AI Studio - UI Components', () => {
  test.skip(
    !process.env.E2E_TEST_USER_EMAIL || !process.env.E2E_TEST_USER_PASSWORD,
    'Skipping AI Studio tests - credentials not configured'
  );

  test('should load the AI Studio page and display main components', async ({ page }) => {
    await page.goto('/ai-studio');
    await page.waitForLoadState('networkidle');

    // Verify that the main tabs are visible
    const generalTab = page.getByRole('tab', { name: /general/i });
    const promptsTab = page.getByRole('tab', { name: /prompts/i });
    const modelTab = page.getByRole('tab', { name: /model/i });

    await expect(generalTab).toBeVisible();
    await expect(promptsTab).toBeVisible();
    await expect(modelTab).toBeVisible();
  });

  test('should open the create agent drawer', async ({ page }) => {
    await page.goto('/ai-studio');
    await page.waitForLoadState('networkidle');

    // Open the create agent drawer and verify its content
    const createAgentButton = page.getByRole('button', { name: /create agent/i });
    const drawer = await openAndVerifyDrawer(page, createAgentButton, /create agent/i);
    await expect(drawer.getByLabel(/name/i)).toBeVisible();
    await expect(drawer.getByLabel(/description/i)).toBeVisible();
  });
});
