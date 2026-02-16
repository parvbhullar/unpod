import { serverFetcher } from '../../../lib/fetcher';
import type { Spaces } from '@unpod/constants/types';

export async function getSpaceDetail(
  spaceSlug: string,
): Promise<Spaces | null> {
  try {
    return (await serverFetcher(`spaces/${spaceSlug}/`)) as Spaces;
  } catch (err) {
    console.log('Error org detail:', err);
  }
  return null;
}
