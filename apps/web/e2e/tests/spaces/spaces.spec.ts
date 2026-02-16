import { test, expect } from '../../fixtures/base.fixture';
import { waitForApiResponse } from '../../utils/api.helper';
import { openAndVerifyDrawer } from '../../utils/ui.helper';
import { createSpace } from '../../utils/actions.helper';
import { APIResponse } from '@playwright/test';

interface SpaceResponse {
  id: string;
  slug: string;
  name: string;
  description: string;
}

test.describe('Spaces Management - Fully Refactored (Robust)', () => {
  test.skip(
    !process.env.E2E_TEST_USER_EMAIL || !process.env.E2E_TEST_USER_PASSWORD,
    'Skipping spaces tests - credentials not configured'
  );

  const spaceName = `Test Space ${Date.now()}`;
  let spaceData: { id: string; slug: string; name: string };

  test.beforeAll(async ({ browser }) => {
    const page = await (await browser.newContext()).newPage();
    spaceData = await createSpace(page, spaceName);
    await page.close();
  });

  test('should update a space and verify API response', async ({ page }) => {
    await page.goto(`/spaces/${spaceData.slug}`);
    await page.waitForLoadState('networkidle');

    const editButton = page.locator('button, .anticon-setting').filter({ hasText: /edit|settings/i }).first();
    const drawer = await openAndVerifyDrawer(page, editButton, /edit space/i);

    const updatedDescription = 'Updated via API test.';

    const [response]: [APIResponse, void, void] = await Promise.all([
      waitForApiResponse(page, `/api/v2/platform/spaces/${spaceData.id}/`, { method: 'PUT' }),
      drawer.locator('textarea, input[name="description"]').fill(updatedDescription),
      drawer.getByRole('button', { name: /save|update/i }).click(),
    ]);

    expect(response.status(), `API call to ${response.url()} failed with status ${response.status()}`).toBe(200);
    const responseBody: SpaceResponse = await response.json();
    expect(responseBody.description).toBe(updatedDescription);

    await expect(page.locator('.ant-message-success')).toBeVisible();
  });
});
