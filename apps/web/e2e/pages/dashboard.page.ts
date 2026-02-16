import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './base.page';
import { URLS } from '../fixtures/test-data';

export class DashboardPage extends BasePage {
  readonly sidebar: Locator;
  readonly mainContent: Locator;
  readonly userMenu: Locator;
  readonly orgSelector: Locator;

  constructor(page: Page) {
    super(page);

    this.sidebar = page.locator('[class*="Sidebar"], [class*="sidebar"]');
    this.mainContent = page
      .locator('[class*="Content"], [class*="content"]')
      .first();
    this.userMenu = page.locator('[class*="UserMenu"], .ant-dropdown-trigger');
    this.orgSelector = page.locator('[class*="OrgSelector"]');
  }

  async goto(): Promise<void> {
    await this.navigate(URLS.dashboard);
    await this.waitForPageLoad();
    await this.waitForSpinnerToDisappear();
  }

  async expectPageLoaded(): Promise<void> {
    await expect(this.mainContent).toBeVisible();
  }

  async navigateToSection(
    section: 'ai-studio' | 'spaces' | 'bridges' | 'knowledge-bases' | 'thread'
  ): Promise<void> {
    const sectionLink = this.page.getByRole('link', {
      name: new RegExp(section.replace('-', ' '), 'i'),
    });
    await sectionLink.click();
    await this.waitForPageLoad();
  }
}
