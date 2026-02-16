import { Page, Locator, expect } from '@playwright/test';

/**
 * Clicks a trigger and verifies that a drawer opens with the expected title.
 * @param page - The Playwright Page object.
 * @param trigger - The Locator for the button/element that opens the drawer.
 * @param drawerTitle - The expected title of the drawer.
 * @returns The Locator for the opened drawer content.
 */
export async function openAndVerifyDrawer(
  page: Page,
  trigger: Locator,
  drawerTitle: string | RegExp
): Promise<Locator> {
  await trigger.click();
  const drawer = page.locator('.ant-drawer-content');
  await expect(drawer).toBeVisible();
  await expect(drawer.locator('.ant-drawer-title')).toContainText(drawerTitle);
  return drawer;
}

/**
 * Clicks a trigger and verifies that a modal opens with the expected title.
 * @param page - The Playwright Page object.
 * @param trigger - The Locator for the button/element that opens the modal.
 * @param modalTitle - The expected title of the modal.
 * @returns The Locator for the opened modal content.
 */
export async function openAndVerifyModal(
  page: Page,
  trigger: Locator,
  modalTitle: string | RegExp
): Promise<Locator> {
  await trigger.click();
  const modal = page.locator('.ant-modal-content');
  await expect(modal).toBeVisible();
  await expect(modal.locator('.ant-modal-title')).toContainText(modalTitle);
  return modal;
}
