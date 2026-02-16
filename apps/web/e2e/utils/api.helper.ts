import { Page, Route, APIResponse } from '@playwright/test';

export interface MockApiOptions {
  status?: number;
  body?: unknown;
  delay?: number;
}

// ... (mockApiResponse and interceptApiCall remain the same) ...
export async function mockApiResponse(
  page: Page,
  urlPattern: string | RegExp,
  options: MockApiOptions = {}
): Promise<void> {
  const { status = 200, body = {}, delay = 0 } = options;

  await page.route(urlPattern, async (route: Route) => {
    if (delay > 0) {
      await new Promise<void>((resolve) => setTimeout(resolve, delay));
    }

    await route.fulfill({
      status,
      contentType: 'application/json',
      body: JSON.stringify(body),
    });
  });
}

export async function interceptApiCall(
  page: Page,
  urlPattern: string | RegExp,
  callback: (request: {
    url: string;
    method: string;
    postData: string | null;
  }) => void
): Promise<void> {
  await page.route(urlPattern, async (route: Route) => {
    const request = route.request();
    callback({
      url: request.url(),
      method: request.method(),
      postData: request.postData(),
    });
    await route.continue();
  });
}


/**
 * Waits for a specific API response by matching URL and optionally the HTTP method.
 * @param page The Playwright Page object.
 * @param urlPattern The URL pattern to match.
 * @param options Optional: timeout and method (e.g., 'POST', 'GET').
 * @returns The full APIResponse object.
 */
export async function waitForApiResponse(
  page: Page,
  urlPattern: string | RegExp,
  options: { timeout?: number; method?: string } = {}
): Promise<APIResponse> {
  const response = await page.waitForResponse(
    (response) => {
      const url = response.url();
      const methodMatch = options.method ? response.request().method() === options.method : true;

      if (!methodMatch) {
        return false;
      }

      if (typeof urlPattern === 'string') {
        return url.includes(urlPattern);
      }
      return urlPattern.test(url);
    },
    { timeout: options.timeout || 30000 }
  );

  return response;
}
