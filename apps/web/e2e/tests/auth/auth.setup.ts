import { test as setup, expect } from '@playwright/test';
import { TEST_USERS, URLS } from '../../fixtures/test-data';

const authFile = 'playwright/.auth/user.json';

setup('authenticate', async ({ page }) => {
  // Skip if credentials not configured
  if (!process.env.E2E_TEST_USER_EMAIL || !process.env.E2E_TEST_USER_PASSWORD) {
    console.log('Skipping auth setup - credentials not configured');
    // Create empty auth state
    await page.context().storageState({ path: authFile });
    return;
  }

  // Navigate to sign in page
  await page.goto(URLS.signin);

  // Wait for page to load
  await page.waitForLoadState('networkidle');

  // Wait for the form to be visible
  await page.waitForSelector('.ant-card', { timeout: 30000 });

  // Fill in credentials using more reliable selectors
  // The first input is email, second is password
  const emailInput = page.locator('input').first();
  const passwordInput = page.locator('input[type="password"]');

  await emailInput.fill(TEST_USERS.valid.email);
  await passwordInput.fill(TEST_USERS.valid.password);

  // Click sign in button
  await page.locator('button[type="submit"]').click();

  // Wait for successful authentication - redirect to dashboard or org
  await page.waitForURL(
    /\/(dashboard|org|spaces|create-org|join-org|business-identity|creating-identity)/,
    { timeout: 30000 }
  );

  // Verify we're logged in by checking for protected content
  await expect(page).toHaveURL(
    /\/(dashboard|org|spaces|create-org|join-org|business-identity|creating-identity)/
  );

  // Save authentication state
  await page.context().storageState({ path: authFile });
});
