import { Page, BrowserContext } from '@playwright/test';
import { TEST_USERS, URLS } from '../fixtures/test-data';

export async function login(
  page: Page,
  email?: string,
  password?: string
): Promise<void> {
  const credentials = {
    email: email || TEST_USERS.valid.email,
    password: password || TEST_USERS.valid.password,
  };

  await page.goto(URLS.signin);
  await page.waitForLoadState('networkidle');

  await page.getByPlaceholder(/email/i).fill(credentials.email);
  await page.locator('input[type="password"]').fill(credentials.password);
  await page.locator('button[type="submit"]').click();

  // Wait for redirect
  await page.waitForURL(
    /\/(dashboard|org|spaces|create-org|join-org|business-identity)/,
    {
      timeout: 30000,
    }
  );
}

export async function logout(page: Page): Promise<void> {
  // Clear cookies and local storage
  const context = page.context();
  await context.clearCookies();
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
}

export async function isAuthenticated(page: Page): Promise<boolean> {
  // Check for token cookie
  const cookies = await page.context().cookies();
  const tokenCookie = cookies.find((c) => c.name === 'token');
  return !!tokenCookie?.value;
}

export async function setAuthCookies(
  context: BrowserContext,
  token: string,
  handle?: string
): Promise<void> {
  await context.addCookies([
    {
      name: 'token',
      value: token,
      domain: 'localhost',
      path: '/',
    },
    ...(handle
      ? [
          {
            name: 'handle',
            value: handle,
            domain: 'localhost',
            path: '/',
          },
        ]
      : []),
  ]);
}
