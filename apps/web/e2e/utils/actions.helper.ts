import { Page, expect } from '@playwright/test';
import { waitForApiResponse } from './api.helper';
import { openAndVerifyModal } from './ui.helper';

/**
 * Creates a new AI Agent via the UI and returns its handle.
 * This is a business-logic helper that encapsulates a full user action.
 * @param page The Playwright Page object.
 * @param agentName The name for the new agent.
 * @returns The handle of the newly created agent.
 */
export async function createAgent(page: Page, agentName: string): Promise<string> {
  await page.goto('/ai-studio/new');
  await page.waitForLoadState('networkidle');

  const [response] = await Promise.all([
    waitForApiResponse(page, '/api/v1/agents/'),
    page.getByLabel(/name/i).fill(agentName),
    page.locator('button').filter({ hasText: /save/i }).click(),
  ]);

  expect(response.status(), `API call to ${response.url()} failed with status ${response.status()}`).toBe(201);
  const responseBody: { handle: string; name: string } = await response.json(); // Explicitly type responseBody
  expect(responseBody.name).toBe(agentName);

  // Wait for navigation to the new agent's page to be complete
  await page.waitForURL(new RegExp(responseBody.handle));

  return responseBody.handle;
}

/**
 * Creates a new Space via the UI and returns its data.
 * This is a business-logic helper that encapsulates a full user action.
 * @param page The Playwright Page object.
 * @param spaceName The name for the new space.
 * @param spaceType The type of space to create (e.g., 'general', 'contact').
 * @returns The API response data for the new space.
 */
export async function createSpace(
  page: Page,
  spaceName: string,
  spaceType: 'general' | 'contact' = 'general'
): Promise<{ id: string; slug: string; name: string }> {
  await page.goto('/spaces/');
  await page.waitForLoadState('networkidle');

  const createButton = page.getByRole('button', { name: /create space|new space/i });
  const modal = await openAndVerifyModal(page, createButton, /create space/i);

  // Select the space type
  await modal.getByRole('button', { name: new RegExp(spaceType, 'i') }).click();

  const [response] = await Promise.all([
    waitForApiResponse(page, '/api/v2/platform/spaces/'),
    modal.getByLabel(/name/i).fill(spaceName),
    modal.getByRole('button', { name: /create|save/i }).click(),
  ]);

  expect(response.status(), `API call to ${response.url()} failed with status ${response.status()}`).toBe(201);
  const responseBody: { id: string; slug: string; name: string } = await response.json(); // Explicitly type responseBody
  expect(responseBody.name).toBe(spaceName);

  // Wait for the UI to reflect the change
  await expect(page.getByText(spaceName)).toBeVisible();

  return responseBody;
}
