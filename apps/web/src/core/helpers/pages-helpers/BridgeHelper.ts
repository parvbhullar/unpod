import { getCookie } from 'cookies-next';
import { httpClient, setAuthToken } from '@unpod/services';
import { isRequestSuccessful } from '@unpod/helpers/ApiHelper';
import type { NextApiRequest, NextApiResponse } from 'next';
import type { Bridge } from '@unpod/constants/types';

type BridgePropsArgs = {
  req: NextApiRequest;
  res: NextApiResponse;
  params: { bridgeSlug?: string };
  removeHeader?: boolean;
};

export const getBridgeProps = async ({ req, res, params }: BridgePropsArgs) => {
  const { bridgeSlug } = params;
  console.log('bridge slug', bridgeSlug);
  const token =
    (getCookie('token', { req, res }) as string | undefined) || null;
  const props: { token: string | null; bridge: Bridge | null } = {
    token,
    bridge: null,
  };

  try {
    if (token) setAuthToken(token);
    const response = await httpClient.get(`telephony/bridges/${bridgeSlug}/`);

    if (isRequestSuccessful(response.status)) {
      props.bridge = response.data.data as Bridge;
    } else {
      props.bridge = response.data.data as Bridge;
    }
  } catch (error) {
    console.log('error: ', error, bridgeSlug);
  }

  // console.log('props: ', props);
  return {
    props,
  };
};
