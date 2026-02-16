import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from '../base.page';
import { URLS } from '../../fixtures/test-data';

export class SignInPage extends BasePage {
  // Locators based on actual SignInForm.js structure
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly rememberMeCheckbox: Locator;
  readonly signInButton: Locator;
  readonly forgotPasswordLink: Locator;
  readonly signUpLink: Locator;
  readonly pageTitle: Locator;
  readonly errorMessage: Locator;
  readonly formCard: Locator;

  constructor(page: Page) {
    super(page);

    // Form card container
    this.formCard = page.locator('.ant-card');

    // The title uses StyledAuthTitle which renders an h3
    this.pageTitle = page.locator('h3').first();

    // Form inputs - AppInput and AppPassword render ant-input components
    this.emailInput = page.locator('input').first();
    this.passwordInput = page.locator('input[type="password"]');

    // Remember me checkbox
    this.rememberMeCheckbox = page.locator('.ant-checkbox-input');

    // Submit button with htmlType="submit"
    this.signInButton = page.locator('button[type="submit"]');

    // Links
    this.forgotPasswordLink = page.locator('a[href*="forgot-password"]');
    this.signUpLink = page.locator('a[href*="signup"]');

    // Error messages - Ant Design form validation and message components
    this.errorMessage = page.locator(
      '.ant-message-error, .ant-form-item-explain-error'
    );
  }

  async goto(): Promise<void> {
    await this.navigate(URLS.signin);
    await this.waitForPageLoad();
  }

  async fillEmail(email: string): Promise<void> {
    await this.emailInput.fill(email);
  }

  async fillPassword(password: string): Promise<void> {
    await this.passwordInput.fill(password);
  }

  async checkRememberMe(): Promise<void> {
    await this.rememberMeCheckbox.check();
  }

  async clickSignIn(): Promise<void> {
    await this.signInButton.click();
  }

  async signIn(
    email: string,
    password: string,
    rememberMe = false
  ): Promise<void> {
    await this.fillEmail(email);
    await this.fillPassword(password);
    if (rememberMe) {
      await this.checkRememberMe();
    }
    await this.clickSignIn();
  }

  async expectPageLoaded(): Promise<void> {
    await expect(this.formCard).toBeVisible();
    await expect(this.emailInput).toBeVisible();
    await expect(this.passwordInput).toBeVisible();
  }

  async expectValidationError(message: string | RegExp): Promise<void> {
    await expect(
      this.page
        .locator('.ant-form-item-explain-error')
        .filter({ hasText: message })
    ).toBeVisible();
  }

  async expectSignInError(): Promise<void> {
    // Wait for either form validation error or toast message
    const errorLocator = this.page.locator(
      '.ant-message-error, .ant-form-item-explain-error, .ant-notification-notice-error'
    );
    await expect(errorLocator.first()).toBeVisible({ timeout: 15000 });
  }

  async clickForgotPassword(): Promise<void> {
    await this.forgotPasswordLink.click();
  }

  async clickSignUp(): Promise<void> {
    await this.signUpLink.click();
  }
}
