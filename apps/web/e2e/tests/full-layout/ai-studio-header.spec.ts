import { test, expect } from '../../fixtures/base.fixture';
import { waitForApiResponse } from '../../utils/api.helper';
import { openAndVerifyDrawer } from '../../utils/ui.helper';
import { createAgent } from '../../utils/actions.helper';
import { APIResponse } from '@playwright/test';

interface AgentResponse {
  handle: string;
  name: string;
  state: string;
}

test.describe('AI Studio - Header Buttons and Menus (Fully Refactored)', () => {
  test.skip(
    !process.env.E2E_TEST_USER_EMAIL || !process.env.E2E_TEST_USER_PASSWORD,
    'Skipping AI Studio header tests - credentials not configured'
  );

  const agentName = `Header Test Agent ${Date.now()}`;
  let agentHandle = '';

  test.beforeAll(async ({ browser }) => {
    const page = await (await browser.newContext()).newPage();
    agentHandle = await createAgent(page, agentName);
    await page.close();
  });

  test.beforeEach(async ({ page }) => {
    await page.goto(`/ai-studio/${agentHandle}`);
    await page.waitForLoadState('networkidle');
  });

  test('should publish an agent and verify API response', async ({ page }) => {
    const publishButton = page.getByRole('button', { name: /publish/i });

    const [response]: [APIResponse, void] = await Promise.all([
      waitForApiResponse(page, `/api/v1/agents/${agentHandle}/`),
      publishButton.click(),
    ]);

    expect(response.status(), `API call to ${response.url()} failed with status ${response.status()}`).toBe(200);
    const responseBody: AgentResponse = await response.json();
    expect(responseBody.state).toBe('published');

    await expect(page.locator('.ant-message-success')).toBeVisible();
  });

  test('should open "Talk to Agent" drawer', async ({ page }) => {
    const talkButton = page.getByRole('button', { name: /talk to agent/i });
    const drawer = await openAndVerifyDrawer(page, talkButton, /agent testing/i);

    await drawer.locator('.ant-drawer-close').click();
    await expect(drawer).not.toBeVisible();
  });
});
