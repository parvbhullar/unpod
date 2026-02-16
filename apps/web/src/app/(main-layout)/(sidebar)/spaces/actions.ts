import { serverFetcher } from '../../../lib/fetcher';
import type { Spaces } from '@unpod/constants/types';

export async function getSpaceDetail(
  spaceSlug: string,
): Promise<Spaces | undefined> {
  try {
    return await serverFetcher<Spaces>(`spaces/${spaceSlug}/`);
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    console.log('Error org detail:', message);
  }
  return undefined;
}
