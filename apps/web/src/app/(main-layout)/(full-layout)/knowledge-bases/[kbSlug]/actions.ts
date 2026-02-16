import { serverFetcher } from '../../../../lib/fetcher';
import type { Spaces } from '@unpod/constants/types';

export async function getKnowledgebase(kbSlug: string): Promise<Spaces> {
  try {
    return (await serverFetcher(`spaces/${kbSlug}/`)) as Spaces;
  } catch (error) {
    console.log('error: ', error);
  }
  return {};
}
