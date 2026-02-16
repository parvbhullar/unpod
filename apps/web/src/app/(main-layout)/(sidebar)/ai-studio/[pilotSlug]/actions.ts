import { serverFetcher } from '../../../../lib/fetcher';
import type { Pilot } from '@unpod/constants/types';

type PilotResponse = {
  space: null;
  pilot_status: string;
  pilot: Pilot | null;
  message?: string;
};

export async function getPilot(pilotSlug: string): Promise<PilotResponse> {
  const props: PilotResponse = {
    space: null,
    pilot_status: '',
    pilot: null,
  };
  try {
    const data = await serverFetcher<Pilot & { message?: string }>(
      `core/pilots/${pilotSlug}/`,
    );
    if (data?.message?.includes('Not Found')) {
      props.pilot_status = 'not_found';
      props.message = data.message;
    } else {
      props.pilot = data as Pilot;
    }
    return props;
  } catch (error) {
    console.log('error: ', error);
  }
  return props;
}
