import { test, expect } from '../../fixtures/base.fixture';

test.describe('Studio & Admin Navigation', () => {
  // Skip all tests in this file if the required environment variables are not set.
  test.skip(
    !process.env.E2E_TEST_USER_EMAIL || !process.env.E2E_TEST_USER_PASSWORD,
    'Skipping Studio/Admin tests - credentials not configured'
  );

  test.beforeEach(async ({ page }) => {
    // Navigate to a page where the AdminMenu is active.
    await page.goto('/org');
    await page.waitForLoadState('networkidle');
  });

  test('should display and navigate the main admin menu links', async ({ page }) => {
    // ... (previous test remains the same)
    const dashboardLink = page.getByTitle('Dashboard');
    await expect(dashboardLink).toBeVisible();
    await dashboardLink.click();
    await page.waitForURL('/org');
    expect(page.url()).toContain('/org');

    const aiStudioLink = page.getByTitle('AI Studio');
    await expect(aiStudioLink).toBeVisible();
    await aiStudioLink.click();
    await page.waitForURL('/ai-studio/**');
    expect(page.url()).toContain('/ai-studio');

    const kbLink = page.getByTitle('Knowledge Base');
    await expect(kbLink).toBeVisible();
    await kbLink.click();
    await page.waitForURL('/knowledge-bases');
    expect(page.url()).toContain('/knowledge-bases');

    const callLogsLink = page.getByTitle('Call Logs');
    await expect(callLogsLink).toBeVisible();
    await callLogsLink.click();
    await page.waitForURL('/call-logs');
    expect(page.url()).toContain('/call-logs');

    const apiKeysLink = page.getByTitle('API Keys');
    await expect(apiKeysLink).toBeVisible();
    await apiKeysLink.click();
    await page.waitForURL('/api-keys');
    expect(page.url()).toContain('/api-keys');
  });

  test('should navigate to a dynamic agent page from AI Studio', async ({ page }) => {
    // Navigate to the AI Studio page first.
    await page.goto('/ai-studio/**');
    await page.waitForLoadState('networkidle');

    // Find the first agent card on the page.
    const firstAgentCard = page.locator('.ant-card').first();
    await expect(firstAgentCard).toBeVisible();

    // Get the agent's handle from the card to predict the URL.
    const agentHandle = await firstAgentCard.locator('[class*="StyledAgentHandle"]').textContent();
    // The handle has an '@' prefix that needs to be removed.
    const expectedHandle = agentHandle?.replace('@', '');

    // Click the edit button on the card.
    await firstAgentCard.getByRole('button', { name: /edit/i }).click();

    // Wait for the URL to change to the dynamic agent page.
    await page.waitForURL(`/ai-studio/${expectedHandle}`);

    // Assert that the URL is correct.
    expect(page.url()).toContain(`/ai-studio/${expectedHandle}`);
  });
});
