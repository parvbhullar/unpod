import { serverFetcher } from '../../../lib/fetcher';
import type { ApiResponse } from '@/types/common';

export async function getOrganizationDetail(
  orgSlug: string,
): Promise<ApiResponse> {
  try {
    return await serverFetcher(`organization/detail/${orgSlug}/`);
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    console.log('Error org detail:', message);
    return { message };
  }
}

export async function getDashboardMatrics(
  domain_handle: string,
): Promise<ApiResponse> {
  try {
    return await serverFetcher(`metrics/organization/`, {
      headers: {
        'Org-Handle': domain_handle,
      },
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    console.log('Error org members:', message);
    return { message };
  }
}
