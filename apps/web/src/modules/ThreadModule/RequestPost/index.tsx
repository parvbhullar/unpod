import { useEffect, useState } from 'react';
import { StyledPlaceHolder, StyledPlaceHolderInner } from './index.styled';
import AppImage from '@unpod/components/next/AppImage';
import { Button, Space, Typography } from 'antd';
import { getDataApi, useInfoViewActionsContext } from '@unpod/providers';
import type { Thread } from '@unpod/constants/types';
import type { ApiResponse } from '@/types/common';

type RequestPostData = Thread & {
  request_token?: string;
  is_requested?: boolean;
};

type RequestPostProps = {
  post?: RequestPostData | null;
};

const RequestPost = ({ post }: RequestPostProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const [myPost, setMyPost] = useState<RequestPostData | null>(post ?? null);

  useEffect(() => {
    if (post) setMyPost(post);
  }, [post]);

  const onRequestAccess = () => {
    if (!myPost?.slug) return;
    getDataApi(`threads/${myPost.slug}/request/`, infoViewActionsContext)
      .then((data) => {
        const res = data as ApiResponse<{ request_token?: string }>;
        if (res.message) infoViewActionsContext.showMessage(res.message);
        setMyPost({
          ...myPost,
          request_token: res.data?.request_token,
          is_requested: true,
        });
      })
      .catch((error) => {
        infoViewActionsContext.showError(error.message);
      });
  };
  const onResendRequest = () => {
    if (!myPost?.slug || !myPost?.request_token) return;
    getDataApi(
      `threads/${myPost.slug}/request/${myPost.request_token}/resend/`,
      infoViewActionsContext,
    )
      .then((data) => {
        const res = data as ApiResponse<{ request_token?: string }>;
        setMyPost({ ...myPost, request_token: res.data?.request_token });
        if (res.message) infoViewActionsContext.showMessage(res.message);
      })
      .catch(() => {
        onRequestAccess();
      });
  };

  return (
    <StyledPlaceHolder>
      <StyledPlaceHolderInner>
        <AppImage
          src={'/images/design-team.png'}
          alt="Design Team"
          width={376}
          height={344}
        />
        <Typography.Title level={3} style={{ marginTop: 32 }}>
          You don&apos;t have access to this post.
        </Typography.Title>

        <Space>
          {myPost?.is_requested ? (
            <>
              {/* <Button type="primary" onClick={onDeleteRequest}>
                Delete Request
              </Button>*/}
              <Button type="primary" onClick={onResendRequest}>
                Resend Request
              </Button>
            </>
          ) : (
            <Button type="primary" onClick={onRequestAccess}>
              Request Access
            </Button>
          )}
        </Space>
      </StyledPlaceHolderInner>
    </StyledPlaceHolder>
  );
};

export default RequestPost;
