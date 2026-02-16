import { test, expect } from '../../fixtures/base.fixture';
import { waitForApiResponse } from '../../utils/api.helper';

test.describe('Knowledge Bases Page', () => {
  // Skip all tests in this file if the required environment variables are not set.
  test.skip(
    !process.env.E2E_TEST_USER_EMAIL || !process.env.E2E_TEST_USER_PASSWORD,
    'Skipping Knowledge Bases tests - credentials not configured'
  );

  test.beforeEach(async ({ page }) => {
    // Navigate to the knowledge bases page before each test.
    await page.goto('/knowledge-bases');
    await page.waitForLoadState('networkidle');
  });

  test('should add a new knowledge base and navigate to it', async ({ page }) => {
    // --- Add Knowledge Base ---
    const addButton = page.getByRole('button', { name: /add/i });
    await expect(addButton).toBeVisible();
    await addButton.click();

    // The "Add" button opens a modal with a form.
    const modal = page.locator('.ant-modal-content');
    await expect(modal).toBeVisible();

    // Fill out the form.
    const kbName = `Test KB ${Date.now()}`;
    await modal.getByLabel(/name/i).fill(kbName);
    await modal.getByLabel(/description/i).fill('This is a test knowledge base.');

    // Click the "Create" button.
    const createButton = modal.getByRole('button', { name: /create/i });
    await createButton.click();

    // Wait for the API call to complete and assert that a success message is shown.
    await waitForApiResponse(page, '**/spaces/');
    await expect(page.locator('.ant-message-success')).toBeVisible();

    // Verify that the page has navigated to the new knowledge base.
    await page.waitForURL(`**/knowledge-bases/**`);
    expect(page.url()).toContain(kbName.toLowerCase().replace(/ /g, '-'));

    // --- Navigate to Knowledge Base ---
    // Go back to the main knowledge bases page.
    await page.goto('/knowledge-bases');
    await page.waitForLoadState('networkidle');

    // Find the newly created knowledge base in the grid and click on it.
    const kbCard = page.getByText(kbName);
    await expect(kbCard).toBeVisible();
    await kbCard.click();

    // Verify that the page has navigated to the correct knowledge base.
    await page.waitForURL(`**/knowledge-bases/**`);
    expect(page.url()).toContain(kbName.toLowerCase().replace(/ /g, '-'));
  });
});
