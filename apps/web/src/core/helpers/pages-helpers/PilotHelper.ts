import { getCookie } from 'cookies-next';
import { httpClient, setAuthToken } from '@unpod/services';
import { isRequestSuccessful } from '@unpod/helpers/ApiHelper';
import type { NextApiRequest, NextApiResponse } from 'next';
import type { Pilot } from '@unpod/constants/types';

type PilotPropsArgs = {
  req: NextApiRequest;
  res: NextApiResponse;
  params: { pilotSlug?: string; superBookSlug?: string };
  removeHeader?: boolean;
};

export const getPilotProps = async ({
  req,
  res,
  params,
  removeHeader,
}: PilotPropsArgs) => {
  console.log('params', params);
  const { pilotSlug, superBookSlug } = params;
  const token =
    (getCookie('token', { req, res }) as string | undefined) || null;
  const props: {
    space: null;
    isPublicView: boolean;
    token: string | null;
    headerProps: { removeHeader: boolean; isListingPage: boolean };
    pilot_status: string;
    pilot?: Pilot | null;
    message?: string;
    error?: string;
  } = {
    space: null,
    isPublicView: true,
    token,
    headerProps: {
      removeHeader: removeHeader || false,
      isListingPage: true,
    },
    pilot_status: '',
  };

  try {
    if (token) setAuthToken(token);
    const response = await httpClient.get(
      `core/pilots/${pilotSlug || superBookSlug}/`,
    );

    if (isRequestSuccessful(response.status)) {
      props.pilot = response.data.data as Pilot;
    } else {
      props.pilot = null;

      if (response.data.message.includes('Not Found'))
        props.pilot_status = 'not_found';
      props.message = response.data.message;
    }
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.log('error: ', message);
    props.error = message;
  }

  return {
    props,
  };
};
