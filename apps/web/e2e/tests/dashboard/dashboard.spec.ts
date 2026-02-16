import { test, expect } from '../../fixtures/base.fixture';

test.describe('Dashboard Page', () => {
  // Skip all tests in this file if the required environment variables are not set.
  test.skip(
    !process.env.E2E_TEST_USER_EMAIL || !process.env.E2E_TEST_USER_PASSWORD,
    'Skipping Dashboard tests - credentials not configured'
  );

  test.beforeEach(async ({ page }) => {
    // Navigate to the dashboard page before each test.
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
  });

  test('should display welcome message, profile cards, and metrics', async ({ page }) => {
    // Verify that the welcome message is visible.
    await expect(page.getByText(/welcome/i)).toBeVisible();

    // Verify that the profile cards are visible and navigate correctly.
    const aiStudioCard = page.getByText(/ai studio/i);
    await expect(aiStudioCard).toBeVisible();
    await aiStudioCard.click();
    await page.waitForURL('**/ai-studio');
    expect(page.url()).toContain('/ai-studio');

    // Go back to the dashboard to test the next card.
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    const knowledgeBasesCard = page.getByText(/knowledge bases/i);
    await expect(knowledgeBasesCard).toBeVisible();
    await knowledgeBasesCard.click();
    await page.waitForURL('**/knowledge-bases');
    expect(page.url()).toContain('/knowledge-bases');

    // Go back to the dashboard to test the metrics.
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Verify that the metrics section is visible.
    await expect(page.getByText(/agents/i)).toBeVisible();
    await expect(page.getByText(/telephony/i)).toBeVisible();
  });
});
