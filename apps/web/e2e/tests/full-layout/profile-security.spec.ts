import { test, expect } from '../../fixtures/base.fixture';
import { waitForApiResponse } from '../../utils/api.helper';

test.describe('Profile Page', () => {
  // Skip all tests in this file if the required environment variables are not set.
  test.skip(
    !process.env.E2E_TEST_USER_EMAIL || !process.env.E2E_TEST_USER_PASSWORD,
    'Skipping Profile tests - credentials not configured'
  );

  // Navigate to the profile page before each test.
  test.beforeEach(async ({ page }) => {
    await page.goto('/profile');
    await page.waitForLoadState('networkidle');
  });

  // Test case for the "Edit Profile" tab.
  test('should allow a user to edit their profile', async ({ page }) => {
    // The "Edit Profile" tab is active by default, so no need to click it.

    const newFirstName = `E2E_Test_FirstName_${Date.now()}`;
    const newLastName = `LastName`;

    // Wait for the API call that saves the profile data.
    const apiResponsePromise = waitForApiResponse(page, 'user-profile/');

    // Fill the form fields using their placeholder text, as visible labels are not used.
    await page.getByPlaceholder('First Name').fill(newFirstName);
    await page.getByPlaceholder('Last Name').fill(newLastName);

    // Click the "Save Profile" button.
    await page.getByRole('button', { name: /save profile/i }).click();

    const response = await apiResponsePromise;

    // Assert that the API call was successful.
    expect(response.status(), `API call to ${response.url()} failed`).toBe(200);

    // Assert that a success message is shown to the user.
    await expect(page.locator('.ant-message-success')).toBeVisible();
  });

  // Test case for the "Change Password" tab.
  test('should allow a user to change their password', async ({ page }) => {
    // Click on the "Change Password" tab to make it active.
    await page.getByRole('tab', { name: /change password/i }).click();

    const newPassword = `NewPassword${Date.now()}`;

    // Wait for the API call that changes the password.
    const apiResponsePromise = waitForApiResponse(page, 'change-password/');

    // Fill the password fields using their placeholder text.
    await page.getByPlaceholder('Old Password').fill(process.env.E2E_TEST_USER_PASSWORD!);
    await page.getByPlaceholder('New Password').fill(newPassword);
    await page.getByPlaceholder('Confirm Password').fill(newPassword);

    // Click the "Update Password" button.
    await page.getByRole('button', { name: /update password/i }).click();

    const response = await apiResponsePromise;

    // Assert that the API call was successful.
    expect(response.status(), `API call to ${response.url()} failed`).toBe(200);
    const responseBody = await response.json();
    expect(responseBody.message).toContain('Password changed successfully');

    // Assert that a success message is shown to the user.
    await expect(page.locator('.ant-message-success')).toBeVisible();
  });

  // Test case for the "Language Preference" tab.
  test('should allow a user to change their language preference', async ({ page }) => {
    // Click on the "Language Preference" tab.
    await page.getByRole('tab', { name: /language preference/i }).click();

    // Wait for the API call that updates the user profile.
    const apiResponsePromise = waitForApiResponse(page, 'user-profile/');

    // Click the dropdown to open the language options.
    await page.getByLabel('Select Language').click();

    // Select a new language from the list.
    await page.getByText('हिन्दी (Hindi)').click();

    // Click the "Save Changes" button.
    await page.getByRole('button', { name: /save changes/i }).click();

    const response = await apiResponsePromise;

    // Assert that the API call was successful.
    expect(response.status(), `API call to ${response.url()} failed`).toBe(200);

    // Assert that a success message is shown to the user.
    await expect(page.locator('.ant-message-success')).toBeVisible();
  });
});
