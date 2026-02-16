import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from '../base.page';
import { URLS } from '../../fixtures/test-data';

export class SignUpPage extends BasePage {
  readonly nameInput: Locator;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly confirmPasswordInput: Locator;
  readonly signUpButton: Locator;
  readonly signInLink: Locator;
  readonly pageTitle: Locator;
  readonly termsCheckbox: Locator;

  constructor(page: Page) {
    super(page);

    this.nameInput = page.getByPlaceholder(/name/i);
    this.emailInput = page.getByPlaceholder(/email/i);
    this.passwordInput = page.locator('input[type="password"]').first();
    this.confirmPasswordInput = page.locator('input[type="password"]').nth(1);
    this.signUpButton = page
      .locator('button[type="submit"]')
      .filter({ hasText: /sign up/i });
    this.signInLink = page.getByRole('link', { name: /sign in/i });
    this.pageTitle = page
      .locator('h3')
      .filter({ hasText: /sign up|create account/i });
    this.termsCheckbox = page.locator('.ant-checkbox-input');
  }

  async goto(): Promise<void> {
    await this.navigate(URLS.signup);
    await this.waitForPageLoad();
  }

  async fillForm(name: string, email: string, password: string): Promise<void> {
    await this.nameInput.fill(name);
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    if (await this.confirmPasswordInput.isVisible()) {
      await this.confirmPasswordInput.fill(password);
    }
  }

  async clickSignUp(): Promise<void> {
    await this.signUpButton.click();
  }

  async expectPageLoaded(): Promise<void> {
    await expect(this.pageTitle).toBeVisible();
    await expect(this.emailInput).toBeVisible();
  }
}
