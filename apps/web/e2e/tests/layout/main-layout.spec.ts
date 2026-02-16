import { test, expect } from '../../fixtures/base.fixture';
import { waitForApiResponse } from '../../utils/api.helper';
import { APIResponse } from '@playwright/test';

interface NotificationResponse {
  read: boolean;
}

test.describe('Main Layout Interactions', () => {
  test.skip(
    !process.env.E2E_TEST_USER_EMAIL || !process.env.E2E_TEST_USER_PASSWORD,
    'Skipping layout tests - credentials not configured'
  );

  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
  });

  test('should open notification drawer and mark notification as read', async ({ page }) => {
    const notificationButton = page.locator('button[aria-label="notifications"]');

    if (await notificationButton.isVisible()) {
        await notificationButton.click();

        const drawer = page.locator('.ant-drawer-content').filter({ hasText: /notifications/i });
        await expect(drawer).toBeVisible();

        const unreadNotification = drawer.locator('.notification-item.unread').first();

        if (await unreadNotification.isVisible()) {
            const [response]: [APIResponse, void] = await Promise.all([
              waitForApiResponse(page, /\/api\/v1\/notifications\/.*\/$/),
              unreadNotification.click(),
            ]);

            expect(response.status(), `API call to ${response.url()} failed with status ${response.status()}`).toBe(200);
            const responseBody: NotificationResponse = await response.json();
            expect(responseBody.read).toBe(true);

            await expect(unreadNotification).not.toHaveClass(/unread/);
        }

        await drawer.locator('button[aria-label="Close"]').click();
        await expect(drawer).not.toBeVisible();
    }
  });

  test('should navigate to dashboard', async ({ page }) => {
    await page.getByRole('link', { name: /dashboard/i }).click();
    await expect(page).toHaveURL(/.*\/org/);
  });

  test('should navigate to AI Studio', async ({ page }) => {
    await page.getByRole('link', { name: /ai studio/i }).click();
    await expect(page).toHaveURL(/.*\/ai-studio/);
  });

  test('should navigate to Knowledge Bases', async ({ page }) => {
    await page.getByRole('link', { name: /knowledge base/i }).click();
    await expect(page).toHaveURL(/.*\/knowledge-bases/);
  });

  test('should navigate to Call Logs', async ({ page }) => {
    await page.getByRole('link', { name: /call logs/i }).click();
    await expect(page).toHaveURL(/.*\/call-logs/);
  });

  test('should navigate to API Keys', async ({ page }) => {
    await page.getByRole('link', { name: /api keys/i }).click();
    await expect(page).toHaveURL(/.*\/api-keys/);
  });
});
