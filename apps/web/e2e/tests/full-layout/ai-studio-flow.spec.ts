import { test, expect } from '../../fixtures/base.fixture';
import { waitForApiResponse } from '../../utils/api.helper';
import { createAgent } from '../../utils/actions.helper';
import { APIResponse } from '@playwright/test';

interface LinkKbResponse {
  success: boolean;
}

test.describe('AI Studio - Full API Workflow', () => {
  test.skip(
    !process.env.E2E_TEST_USER_EMAIL || !process.env.E2E_TEST_USER_PASSWORD,
    'Skipping AI Studio flow tests - credentials not configured'
  );

  let agentHandle: string;

  test.beforeAll(async ({ browser }) => {
    const page = await (await browser.newContext()).newPage();
    agentHandle = await createAgent(page, `API Flow Agent ${Date.now()}`);
    await page.close();
  });

  test('should link and unlink a knowledge base and verify API calls', async ({ page }) => {
    await page.goto(`/ai-studio/${agentHandle}`);
    await page.waitForLoadState('networkidle');

    const kbTab = page.getByRole('tab', { name: /knowledge/i });
    await kbTab.click();

    const addKbButton = page.getByRole('button', { name: /add|link knowledge base/i });
    await addKbButton.click();
    const modal = page.locator('.ant-modal-content');

    const firstKb = modal.locator('.kb-list-item, .resource-item').first();
    const kbName = await firstKb.locator('.kb-name, .resource-title').textContent();

    const [linkResponse]: [APIResponse, void] = await Promise.all([
      waitForApiResponse(page, `/api/v1/agents/${agentHandle}/kb/`),
      firstKb.getByRole('button', { name: /link|add/i }).click(),
    ]);

    expect(linkResponse.status(), `API call to ${linkResponse.url()} failed with status ${linkResponse.status()}`).toBe(200);
    const linkResponseBody: LinkKbResponse = await linkResponse.json();
    expect(linkResponseBody.success).toBe(true);

    await modal.locator('.ant-modal-close').click();
    await expect(page.getByText(kbName || ' ')).toBeVisible();

    const linkedKbRow = page.locator('.ant-table-row').filter({ hasText: kbName || ' ' });
    const unlinkButton = linkedKbRow.getByRole('button', { name: /unlink|remove/i });

    const [unlinkResponse]: [APIResponse, void] = await Promise.all([
      waitForApiResponse(page, `/api/v1/agents/${agentHandle}/kb/`),
      unlinkButton.click(),
    ]);

    expect(unlinkResponse.status(), `API call to ${unlinkResponse.url()} failed with status ${unlinkResponse.status()}`).toBe(204);
    await expect(page.getByText(kbName || ' ')).not.toBeVisible();
  });
});
