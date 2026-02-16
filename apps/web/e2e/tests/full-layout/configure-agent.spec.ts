import { test, expect } from '../../fixtures/base.fixture';

test.describe('Configure Agent - Full API Verification', () => {
  test.skip(
    !process.env.E2E_TEST_USER_EMAIL || !process.env.E2E_TEST_USER_PASSWORD,
    'Skipping configure agent tests - credentials not configured'
  );

  const agentName = `Test Agent ${Date.now()}`;

  test('should create a new agent and verify API response', async ({ page }) => {
    await page.goto('/ai-studio/new');
    await page.waitForLoadState('networkidle');

    // Start waiting for the POST request
    const apiResponsePromise = page.waitForResponse(
      (res) => res.url().includes('/api/agents') && res.method() === 'POST'
    );

    // Fill and submit
    await page.getByLabel(/name/i).fill(agentName);
    await page.getByLabel(/description/i).fill('Initial agent description.');
    await page.locator('button').filter({ hasText: /save/i }).click();

    // Verify API response
    const response = await apiResponsePromise;
    expect(response.status()).toBe(201);
    const responseBody = await response.json();
    expect(responseBody.name).toBe(agentName);

    // Verify UI update
    await page.waitForURL(new RegExp(`/ai-studio/${responseBody.handle}`));
    await expect(page.locator('.ant-message-success')).toBeVisible();
  });

  test('should update an existing agent and verify API response', async ({ page }) => {
    // Navigate to an existing agent
    await page.goto('/ai-studio/some-existing-agent-handle'); // Adjust this to a real agent
    await page.waitForLoadState('networkidle');

    // Start waiting for the PUT request
    const apiResponsePromise = page.waitForResponse(
      (res) => res.url().includes('/api/agents/') && res.method() === 'PUT'
    );

    // Update a field
    const updatedPrompt = 'This is the updated agent prompt.';
    await page.getByRole('tab', { name: /persona/i }).click();
    await page.locator('textarea[name="prompt"]').fill(updatedPrompt);
    await page.locator('button').filter({ hasText: /save/i }).nth(1).click();

    // Verify API response
    const response = await apiResponsePromise;
    expect(response.status()).toBe(200);
    const responseBody = await response.json();
    expect(responseBody.prompt).toBe(updatedPrompt);

    // Verify UI update
    await expect(page.locator('.ant-message-success')).toBeVisible();
  });
});
