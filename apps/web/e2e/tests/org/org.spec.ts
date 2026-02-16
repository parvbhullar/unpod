import { test, expect } from '../../fixtures/base.fixture';
import { waitForApiResponse } from '../../utils/api.helper';
import { APIResponse } from '@playwright/test';

interface OrgResponse {
  slug: string;
  name: string;
}

interface InviteResponse {
  email: string;
}

test.describe('Organization - Full Interaction & API Verification (Robust)', () => {
  test.skip(
    !process.env.E2E_TEST_USER_EMAIL || !process.env.E2E_TEST_USER_PASSWORD,
    'Skipping org tests - credentials not configured'
  );

  const orgName = `Full API Test Org ${Date.now()}`;
  let orgSlug: string;

  test.beforeAll(async ({ browser }) => {
    const page = await (await browser.newContext()).newPage();
    await page.goto('/create-org');

    const [apiResponse]: [APIResponse, void, void] = await Promise.all([
      waitForApiResponse(page, '/api/v2/platform/orgs/'),
      page.getByLabel(/organization name/i).fill(orgName),
      page.getByRole('button', { name: /create/i }).click(),
    ]);

    expect(apiResponse.status(), `API call to ${apiResponse.url()} failed with status ${apiResponse.status()}`).toBe(201);
    const responseBody: OrgResponse = await apiResponse.json();
    orgSlug = responseBody.slug;

    await page.close();
  });

  test('should invite a new member and verify API call', async ({ page }) => {
    await page.goto(`/org/${orgSlug}/settings`);
    await page.getByRole('tab', { name: /members/i }).click();

    const inviteButton = page.getByRole('button', { name: /invite member/i });
    await inviteButton.click();
    const modal = page.locator('.ant-modal-content');

    const inviteEmail = `invite-${Date.now()}@example.com`;

    const [apiResponse]: [APIResponse, void, void] = await Promise.all([
      waitForApiResponse(page, `/api/v2/platform/orgs/${orgSlug}/invites/`),
      modal.getByLabel(/email/i).fill(inviteEmail),
      modal.getByRole('button', { name: /send invite/i }).click(),
    ]);

    expect(apiResponse.status(), `API call to ${apiResponse.url()} failed with status ${apiResponse.status()}`).toBe(200);
    const responseBody: InviteResponse = await apiResponse.json();
    expect(responseBody.email).toBe(inviteEmail);

    await expect(page.getByText(inviteEmail)).toBeVisible();
  });
});
