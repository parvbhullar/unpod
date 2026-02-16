import { test, expect } from '../../fixtures/base.fixture';

test.describe('Main Navigation', () => {
  // Skip all tests in this file if the required environment variables are not set.
  test.skip(
    !process.env.E2E_TEST_USER_EMAIL || !process.env.E2E_TEST_USER_PASSWORD,
    'Skipping Navigation tests - credentials not configured'
  );

  // A beforeEach for desktop viewports
  test.describe('Desktop Navigation', () => {
    test.beforeEach(async ({ page }) => {
      // Navigate to a known page that uses the main layout
      await page.goto('/profile');
      await page.waitForLoadState('networkidle');
    });

    test('should display and navigate the main AI menu links', async ({ page }) => {
      // Verify the "Chat" link is visible and navigates correctly.
      const chatLink = page.getByTitle('Chat');
      await expect(chatLink).toBeVisible();
      await chatLink.click();
      await page.waitForURL('**/chat/**');
      expect(page.url()).toContain('/chat/');

      // Verify the "Calls" link is visible and navigates correctly.
      const callsLink = page.getByTitle('Calls');
      await expect(callsLink).toBeVisible();
      await callsLink.click();
      await page.waitForURL('**/call/**');
      expect(page.url()).toContain('/call/');

      // Verify the "Analytics" link is visible and navigates correctly.
      const analyticsLink = page.getByTitle('Analytics');
      await expect(analyticsLink).toBeVisible();
      await analyticsLink.click();
      await page.waitForURL('**/analytics/**');
      expect(page.url()).toContain('/analytics/');
    });

    test('should open the hub selection popover', async ({ page }) => {
      // Click the organization avatar to open the popover.
      await page.locator('.org-avatar').click();

      // Verify that the popover is visible.
      const popover = page.locator('.ant-popover-inner');
      await expect(popover).toBeVisible();

      // Check for the presence of either the organization list or the create/join button.
      const orgList = popover.locator('.ant-menu-item');
      const createOrgButton = popover.getByText(/create an organization/i);
      const joinOrgButton = popover.getByText(/join an organization/i);

      // This assertion checks that at least one of these expected elements is present.
      await expect(
        orgList.first().or(createOrgButton).or(joinOrgButton)
      ).toBeVisible();
    });

    test('should display user info dropdown and handle logout', async ({ page }) => {
      // Hover over the user avatar to trigger the dropdown.
      await page.locator('.user-profile').hover();

      // Verify that the dropdown menu is visible.
      const dropdownMenu = page.locator('.ant-dropdown:not(.ant-dropdown-hidden)');
      await expect(dropdownMenu).toBeVisible();

      // Verify the presence of key menu items.
      await expect(dropdownMenu.getByText(/profile/i)).toBeVisible();
      await expect(dropdownMenu.getByText(/billing/i)).toBeVisible();
      const signOutButton = dropdownMenu.getByText(/sign out/i);
      await expect(signOutButton).toBeVisible();

      // Click the "Sign Out" button.
      await signOutButton.click();

      // Wait for the page to redirect after logout.
      // The app redirects to either '/' or '/auth/signin'.
      await page.waitForURL((url) => url.pathname === '/' || url.pathname === '/auth/signin');

      // Assert that the final URL is one of the expected post-logout destinations.
      expect(page.url()).toMatch(/\/|(\/auth\/signin)$/);
    });
  });

  // A describe block specifically for mobile navigation tests
  test.describe('Mobile Navigation', () => {
    test.beforeEach(async ({ page }) => {
      // Set the viewport to a mobile size for all tests in this block.
      await page.setViewportSize({ width: 375, height: 667 });
      // Navigate to a stable root page.
      await page.goto('/profile');
      await page.waitForLoadState('networkidle');
    });

    test('should open the drawer menu on mobile', async ({ page }) => {
      // From the profile page, click a link to navigate to a page that has a drawer.
      const callsLink = page.getByTitle('Calls');
      await callsLink.click();

      // Wait for the navigation to the calls page to complete.
      await page.waitForURL('**/call/**');

      // Now on the correct page, find and click the drawer trigger icon.
      // The icon is an <MdOutlineMenu />, which Ant Design wraps in a span.
      await page.locator('span[aria-label="menu"]').click();

      // Verify that the drawer is visible by checking for the drawer body.
      const drawer = page.locator('.ant-drawer-body');
      await expect(drawer).toBeVisible();
    });
  });
});
