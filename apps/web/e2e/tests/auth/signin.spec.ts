import { test, expect } from '../../fixtures/base.fixture';
import { TEST_USERS } from '../../fixtures/test-data';
import { APIResponse } from '@playwright/test';

interface UserResponse {
  user: { email: string };
  token: string;
}

test.describe('Sign In', () => {
  test.skip(
    !process.env.E2E_TEST_USER_EMAIL || !process.env.E2E_TEST_USER_PASSWORD,
    'Skipping auth tests - credentials not configured'
  );

  test('should successfully sign in and be redirected to the dashboard', async ({
    signInPage,
    page,
  }) => {
    await signInPage.goto();

    const [apiResponse]: [APIResponse, void] = await Promise.all([
      page.waitForResponse(
        (res) => res.url().includes('/api/v1/auth/login/') && res.request().method() === 'POST'
      ),
      signInPage.signIn(TEST_USERS.valid.email, TEST_USERS.valid.password),
    ]);

    expect(apiResponse.status(), `API call to ${apiResponse.url()} failed with status ${apiResponse.status()}`).toBe(200);
    const responseBody: UserResponse = await apiResponse.json();
    expect(responseBody.user.email).toBe(TEST_USERS.valid.email);
    expect(responseBody.token).toBeDefined();

    // After sign-in, users are typically redirected to a dashboard page.
    await page.waitForURL(/.*\/dashboard/);
    await expect(page).toHaveURL(/.*\/dashboard/);
  });

  test('should show an error message with incorrect password', async ({
    signInPage,
  }) => {
    await signInPage.goto();
    await signInPage.signIn(TEST_USERS.valid.email, 'wrong-password');

    // Use the page object model's method to check for sign-in errors.
    await signInPage.expectSignInError();
  });
});
