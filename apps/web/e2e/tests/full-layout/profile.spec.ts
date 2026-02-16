import { test, expect } from '../../fixtures/base.fixture';

test.describe('User Profile', () => {
  test.skip(
    !process.env.E2E_TEST_USER_EMAIL || !process.env.E2E_TEST_USER_PASSWORD,
    'Skipping profile tests - credentials not configured'
  );

  test('should display user profile information', async ({ page }) => {
    await page.goto('/profile/');
    await page.waitForLoadState('networkidle');

    // Verify profile header
    await expect(page.locator('h1, h2').filter({ hasText: /profile/i })).toBeVisible();

    // Check that email is visible and disabled (usually email can't be changed easily)
    const emailInput = page.locator('input[type="email"]');
    await expect(emailInput).toBeVisible();
    await expect(emailInput).toBeDisabled();
  });

  test('should allow updating profile name', async ({ page }) => {
    await page.goto('/profile/');
    await page.waitForLoadState('networkidle');

    const newName = `User ${Date.now()}`;
    const nameInput = page.getByLabel(/name|full name/i).first();

    // Clear and fill new name
    await nameInput.clear();
    await nameInput.fill(newName);

    // Save changes
    const saveButton = page.getByRole('button', { name: /save|update/i });
    await saveButton.click();

    // Verify success message
    await expect(page.locator('.ant-message-success, .toast-success')).toBeVisible();

    // Reload and verify persistence
    await page.reload();
    await page.waitForLoadState('networkidle');
    await expect(nameInput).toHaveValue(newName);
  });

  test('should allow uploading a profile picture', async ({ page }) => {
    await page.goto('/profile/');
    await page.waitForLoadState('networkidle');

    // This is a bit tricky as it involves file upload.
    // We'll look for the file input.
    const fileInput = page.locator('input[type="file"]');

    // Only run if file input is present
    if (await fileInput.count() > 0) {
        // Create a dummy image buffer
        const buffer = Buffer.from('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7', 'base64');

        await fileInput.setInputFiles({
            name: 'avatar.png',
            mimeType: 'image/png',
            buffer: buffer
        });

        // Wait for upload to complete (usually automatic or requires save)
        // If there's a save button, click it
        const saveButton = page.getByRole('button', { name: /save|update/i });
        if (await saveButton.isVisible()) {
            await saveButton.click();
        }

        // Verify success message
        await expect(page.locator('.ant-message-success, .toast-success')).toBeVisible();
    }
  });
});
