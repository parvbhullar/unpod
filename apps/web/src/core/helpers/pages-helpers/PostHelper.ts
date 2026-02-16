import { getCookie } from 'cookies-next';
import { httpClient, setAuthToken, setOrgHeader } from '@unpod/services';
import { isRequestSuccessful } from '@unpod/helpers/ApiHelper';
import { POST_TYPE } from '@unpod/constants/AppEnums';
import type { NextApiRequest, NextApiResponse } from 'next';
import type { Spaces, Thread } from '@unpod/constants/types';

type PostPropsArgs = {
  req: NextApiRequest;
  res: NextApiResponse;
  params: { postSlug?: string; orgSlug?: string };
  removeHeader?: boolean;
  isView?: boolean;
  isEdit?: boolean;
};

export const getPostProps = async ({
  req,
  res,
  params,
  removeHeader,
  isView,
  isEdit,
}: PostPropsArgs) => {
  const { postSlug, orgSlug } = params;
  const token =
    (getCookie('token', { req, res }) as string | undefined) || null;

  const props: {
    space: Spaces | null;
    post: Thread | null;
    isPublicView: boolean;
    token: string | null;
    headerProps: {
      removeHeader: boolean;
      token: string | null;
      space?: Spaces;
      post?: Thread;
    };
    isEdit: boolean;
    notFound?: boolean;
  } = {
    space: null,
    post: null,
    isPublicView: true,
    token,
    headerProps: {
      removeHeader: removeHeader || false,
      token,
    },
    isEdit: isEdit || false,
  };

  try {
    if (token) setAuthToken(token);
    if (orgSlug) setOrgHeader(orgSlug);
    const response = await httpClient.get(`threads/${postSlug}/detail/`);

    if (isRequestSuccessful(response.status) && response.data.data) {
      const post = response.data.data as Thread;

      if (isView && post?.post_status === 'draft' && token) {
        return {
          redirect: {
            destination: `/thread/${postSlug}/edit`,
          },
        };
      }

      if (
        isEdit &&
        (post?.post_type === POST_TYPE.TASK ||
          post?.post_type === POST_TYPE.ASK)
      ) {
        return {
          redirect: {
            destination: `/thread/${postSlug}/`,
          },
        };
      }

      props.space = post.space ?? null;
      props.post = post;
      props.headerProps = {
        ...props.headerProps,
        space: post.space ?? undefined,
        post: post,
      };
    } else if (response.data.data) {
      const post = response.data.data as Thread;
      if (post.slug) {
        if (isView && post?.post_status === 'draft' && token) {
          return {
            redirect: {
              destination: `/thread/${postSlug}/edit`,
            },
          };
        }

        if (
          isEdit &&
          (post?.post_type === POST_TYPE.TASK ||
            post?.post_type === POST_TYPE.ASK)
        ) {
          return {
            redirect: {
              destination: `/thread/${postSlug}/`,
            },
          };
        }

        props.space = post.space ?? null;
        props.post = post;
        props.headerProps = {
          ...props.headerProps,
          space: post.space ?? undefined,
          post: post,
        };
      } else {
        props.notFound = true;
      }
    } else {
      props.notFound = true;
    }
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.log(' error: ', message);

    return {
      props: {
        notFound: true,
      },
    };
  }

  // console.log('props: ', props);
  if (!props.post) {
    return {
      props: {
        notFound: true,
      },
    };
  }

  // console.log('props: ', props);
  return {
    props,
  };
};
