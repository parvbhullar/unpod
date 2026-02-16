import { test as base, expect } from '@playwright/test';
import { SignInPage } from '../pages/auth/signin.page';
import { SignUpPage } from '../pages/auth/signup.page';
import { DashboardPage } from '../pages/dashboard.page';

// Define custom fixtures
type CustomFixtures = {
  signInPage: SignInPage;
  signUpPage: SignUpPage;
  dashboardPage: DashboardPage;
};

// Extend base test with custom fixtures
export const test = base.extend<CustomFixtures>({
  signInPage: async ({ page }, use) => {
    const signInPage = new SignInPage(page);
    await use(signInPage);
  },

  signUpPage: async ({ page }, use) => {
    const signUpPage = new SignUpPage(page);
    await use(signUpPage);
  },

  dashboardPage: async ({ page }, use) => {
    const dashboardPage = new DashboardPage(page);
    await use(dashboardPage);
  },
});

export { expect };
