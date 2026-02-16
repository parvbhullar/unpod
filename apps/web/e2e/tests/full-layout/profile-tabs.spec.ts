import { test, expect, Page } from '@playwright/test';
import { TEST_USERS } from '../../fixtures/test-data';
import { SignInPage } from '../../pages/auth/signin.page';

// Helper function to reduce repetition
const navigateToProfile = async (page: Page, signInPage: SignInPage): Promise<void> => {
  await signInPage.goto();
  await signInPage.signIn(TEST_USERS.valid.email, TEST_USERS.valid.password);
  await page.waitForURL(/.*\/dashboard/);
  await page.goto('/profile');
  await page.waitForLoadState('networkidle');
};

test.describe('Profile Page Tabs', () => {
  let page: Page;
  let signInPage: SignInPage;

  test.beforeEach(async ({ browser }) => {
    const context = await browser.newContext();
    page = await context.newPage();
    signInPage = new SignInPage(page);
    await navigateToProfile(page, signInPage);
  });

  test('should switch between tabs on the profile page', async () => {
    // Verify that the "Edit Profile" tab is active by default
    const editProfileTab = page.getByRole('tab', { name: /edit profile/i });
    await expect(editProfileTab).toBeVisible();
    await expect(editProfileTab).toHaveAttribute('aria-selected', 'true');
    // Check for a unique element within the "Edit Profile" tab content
    await expect(page.getByRole('button', { name: /save changes/i })).toBeVisible();

    // Click on the "Change Password" tab
    const changePasswordTab = page.getByRole('tab', { name: /change password/i });
    await changePasswordTab.click();

    // Verify that the "Change Password" tab is active
    await expect(changePasswordTab).toHaveAttribute('aria-selected', 'true');
    await expect(editProfileTab).toHaveAttribute('aria-selected', 'false');
    // Check for a unique element within the "Change Password" tab content
    await expect(page.getByLabel(/old password/i)).toBeVisible();

    // Click on the "Language Preference" tab
    const languagePreferenceTab = page.getByRole('tab', { name: /language preference/i });
    await languagePreferenceTab.click();

    // Verify that the "Language Preference" tab is active
    await expect(languagePreferenceTab).toHaveAttribute('aria-selected', 'true');
    await expect(changePasswordTab).toHaveAttribute('aria-selected', 'false');
    // Check for a unique element within the "Language Preference" tab content
    await expect(page.getByText(/select your preferred language/i)).toBeVisible();
  });
});
