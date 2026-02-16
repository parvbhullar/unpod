// Test user credentials - should be environment variables in CI
export const TEST_USERS = {
  valid: {
    email: process.env.E2E_TEST_USER_EMAIL || 'test@example.com',
    password: process.env.E2E_TEST_USER_PASSWORD || 'TestPassword123!',
  },
  invalid: {
    email: 'invalid@example.com',
    password: 'wrongpassword',
  },
};

// URLs - note: Next.js uses trailing slashes in this project
export const URLS = {
  home: '/',
  signin: '/auth/signin/',
  signup: '/auth/signup/',
  forgotPassword: '/auth/forgot-password/',
  createOrg: '/create-org/',
  joinOrg: '/join-org/',
  dashboard: '/dashboard/',
  org: '/org/',
  aiStudio: '/ai-studio/',
  spaces: '/spaces/',
  bridges: '/bridges/',
  knowledgeBases: '/knowledge-bases/',
  thread: '/thread/',
  privacyPolicy: '/privacy-policy/',
  termsAndConditions: '/terms-and-conditions/',
};

// Timeouts
export const TIMEOUTS = {
  navigation: 30000,
  animation: 500,
  apiResponse: 10000,
};
