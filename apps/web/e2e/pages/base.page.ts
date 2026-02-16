import { Page, Locator, expect } from '@playwright/test';

export abstract class BasePage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async navigate(path: string): Promise<void> {
    await this.page.goto(path);
  }

  async waitForPageLoad(): Promise<void> {
    await this.page.waitForLoadState('networkidle');
  }

  async getTitle(): Promise<string> {
    return this.page.title();
  }

  async takeScreenshot(name: string): Promise<void> {
    await this.page.screenshot({ path: `screenshots/${name}.png` });
  }

  // Common UI elements (Ant Design specific)
  async waitForSpinnerToDisappear(): Promise<void> {
    const spinner = this.page.locator('.ant-spin-spinning');
    if (await spinner.isVisible({ timeout: 1000 }).catch(() => false)) {
      await spinner.waitFor({ state: 'hidden', timeout: 30000 });
    }
  }

  async waitForNotification(
    type: 'success' | 'error' | 'info' | 'warning'
  ): Promise<Locator> {
    const notification = this.page.locator(`.ant-message-${type}`);
    await notification.waitFor({ state: 'visible' });
    return notification;
  }

  async closeNotification(): Promise<void> {
    const closeBtn = this.page.locator('.ant-message-notice-close');
    if (await closeBtn.isVisible({ timeout: 1000 }).catch(() => false)) {
      await closeBtn.click();
    }
  }
}
