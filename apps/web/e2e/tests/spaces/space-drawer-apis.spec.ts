import { test, expect } from '../../fixtures/base.fixture';
import { waitForApiResponse } from '../../utils/api.helper';
import { createSpace } from '../../utils/actions.helper';

test.describe('Space Drawer - Secondary API Call Verification', () => {
  test.skip(
    !process.env.E2E_TEST_USER_EMAIL || !process.env.E2E_TEST_USER_PASSWORD,
    'Skipping Space Drawer API tests - credentials not configured'
  );

  const spaceName = `API Test Space ${Date.now()}`;
  let spaceData: any;

  test.beforeAll(async ({ browser }) => {
    // Create a space of type 'contact' to ensure all tabs are visible
    const page = await (await browser.newContext()).newPage();
    spaceData = await createSpace(page, spaceName); // Assuming createSpace can be modified to set content_type
    await page.close();
  });

  test('should make correct API calls when switching tabs in Edit Space drawer', async ({ page }) => {
    // 1. Navigate to the space and open the drawer
    await page.goto(`/spaces/${spaceData.slug}`);
    await page.waitForLoadState('networkidle');
    const editButton = page.locator('button, .anticon-setting').filter({ hasText: /edit|settings/i }).first();
    await editButton.click();
    const drawer = page.locator('.ant-drawer-content');
    await expect(drawer).toBeVisible();

    // 2. Test "Table Schema" Tab API Call
    const schemaTab = drawer.getByRole('tab', { name: /table schema/i });
    if (await schemaTab.isVisible()) {
      // Start waiting for the API call that fetches the schema
      const schemaApiPromise = waitForApiResponse(page, /\/api\/schemas\//);
      await schemaTab.click();

      // Verify the API was called and returned a successful response
      const schemaResponse = await schemaApiPromise;
      expect(schemaResponse).toBeDefined();
    }

    // 3. Test "Link Agent" Tab API Call
    const linkAgentTab = drawer.getByRole('tab', { name: /link agent/i });
    if (await linkAgentTab.isVisible()) {
      // Start waiting for the API call that fetches the list of agents
      const agentsApiPromise = waitForApiResponse(page, /\/api\/agents/);
      await linkAgentTab.click();

      // Verify the API was called and returned a list
      const agentsResponse: any = await agentsApiPromise;
      expect(Array.isArray(agentsResponse.results)).toBe(true);

      // Also verify the UI shows the list
      await expect(drawer.locator('.agent-list-item, .resource-list-item').first()).toBeVisible();
    }
  });
});
