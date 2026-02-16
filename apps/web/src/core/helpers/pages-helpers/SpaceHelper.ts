import { getCookie } from 'cookies-next';
import { httpClient, setAuthToken } from '@unpod/services';
import { isRequestSuccessful } from '@unpod/helpers/ApiHelper';
import type { NextApiRequest, NextApiResponse } from 'next';
import type { Spaces } from '@unpod/constants/types';

type SpacePropsArgs = {
  req: NextApiRequest;
  res: NextApiResponse;
  params: { spaceSlug?: string; orgSlug?: string };
  removeHeader?: boolean;
};

export const getSpaceProps = async ({
  req,
  res,
  params,
  removeHeader,
}: SpacePropsArgs) => {
  const { spaceSlug, orgSlug } = params;
  console.log('space slug', spaceSlug);
  const token =
    (getCookie('token', { req, res }) as string | undefined) || null;
  const props: {
    space: Spaces | null;
    isPublicView: boolean;
    orgSlug: string | null;
    token: string | null;
    headerProps: {
      removeHeader: boolean;
      isListingPage: boolean;
      space?: Spaces;
    };
  } = {
    space: null,
    isPublicView: true,
    orgSlug: orgSlug || null,
    token,
    headerProps: {
      removeHeader: removeHeader || false,
      isListingPage: true,
    },
  };

  try {
    if (token) setAuthToken(token);
    const response = await httpClient.get(`spaces/${spaceSlug}/`);

    if (isRequestSuccessful(response.status)) {
      const space = response.data.data as Spaces;
      props.space = space;
      props.headerProps = {
        ...props.headerProps,
        space: space,
        isListingPage: space.space_type === 'general',
      };
    } else {
      const space = response.data.data as Spaces;
      props.space = space;
      props.headerProps = {
        ...props.headerProps,
        space,
        isListingPage: space.space_type === 'general',
      };
    }
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.log('error: ', message, spaceSlug);
  }

  // console.log('props: ', props);
  return {
    props,
  };
};
