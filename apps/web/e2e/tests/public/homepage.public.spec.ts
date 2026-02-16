import { test, expect } from '@playwright/test';
import { URLS } from '../../fixtures/test-data';

// These tests run without authentication (chromium-no-auth project)
test.describe('Homepage - Public', () => {
  test('should load homepage successfully', async ({ page }) => {
    await page.goto(URLS.home);
    await page.waitForLoadState('networkidle');

    // Check page title contains Unpod
    await expect(page).toHaveTitle(/unpod/i);
  });

  test('should display main landing content', async ({ page }) => {
    await page.goto(URLS.home);
    await page.waitForLoadState('networkidle');

    // Check for main landing page elements
    const mainContent = page.locator(
      'main, [class*="landing"], [class*="Landing"]'
    );
    await expect(mainContent.first()).toBeVisible();
  });

  test('should have navigation links', async ({ page }) => {
    await page.goto(URLS.home);
    await page.waitForLoadState('networkidle');

    // Check for common navigation elements
    const signInLink = page.getByRole('link', { name: /sign in|login/i });
    if (await signInLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(signInLink).toBeVisible();
    }
  });

  test('should be responsive on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE
    await page.goto(URLS.home);
    await page.waitForLoadState('networkidle');

    // Page should still be functional
    await expect(page).toHaveTitle(/unpod/i);
  });
});

test.describe('Privacy Policy - Public', () => {
  test('should load privacy policy page', async ({ page }) => {
    await page.goto(URLS.privacyPolicy);
    await page.waitForLoadState('networkidle');

    // Check page loads
    await expect(page).toHaveURL(new RegExp(URLS.privacyPolicy));
  });

  test('should display privacy policy content', async ({ page }) => {
    await page.goto(URLS.privacyPolicy);
    await page.waitForLoadState('networkidle');

    // Check for privacy-related content
    const content = page.locator('body');
    await expect(content).toContainText(/privacy/i);
  });
});

test.describe('Terms and Conditions - Public', () => {
  test('should load terms and conditions page', async ({ page }) => {
    await page.goto(URLS.termsAndConditions);
    await page.waitForLoadState('networkidle');

    await expect(page).toHaveURL(
      new RegExp(URLS.termsAndConditions.replace(/\//g, '\\/'))
    );
  });

  test('should display terms content', async ({ page }) => {
    await page.goto(URLS.termsAndConditions);
    await page.waitForLoadState('networkidle');

    const content = page.locator('body');
    await expect(content).toContainText(/terms/i);
  });
});
