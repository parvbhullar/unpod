import { serverFetcher } from '../../../../lib/fetcher';
import type { Bridge } from '@unpod/constants/types';

export async function getBridge(bridgeSlug: string): Promise<Bridge> {
  try {
    return (await serverFetcher(`telephony/bridges/${bridgeSlug}/`)) as Bridge;
  } catch (error) {
    console.log('error: ', error);
  }
  return {};
}
