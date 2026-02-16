import { useEffect, useState } from 'react';
import { StyledPlaceHolder, StyledPlaceHolderInner } from './index.styled';
import AppImage from '@unpod/components/next/AppImage';
import { Button, Space, Typography } from 'antd';
import { getDataApi, useInfoViewActionsContext } from '@unpod/providers';

type RequestPostProps = {
  post: any;
};

const RequestPost = ({ post }: RequestPostProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const [myPost, setMyPost] = useState<any>(post);

  useEffect(() => {
    if (post) setMyPost(post);
  }, [post]);

  const onRequestAccess = () => {
    getDataApi(`threads/${myPost.slug}/request/`, infoViewActionsContext)
      .then((data: any) => {
        infoViewActionsContext.showMessage(data.message);
        setMyPost({
          ...myPost,
          request_token: data.data.request_token,
          is_requested: true,
        });
      })
      .catch((error: any) => {
        infoViewActionsContext.showError(error.message);
      });
  };
  const onResendRequest = () => {
    getDataApi(
      `threads/${myPost.slug}/request/${myPost.request_token}/resend/`,
      infoViewActionsContext,
    )
      .then((data: any) => {
        setMyPost({ ...myPost, request_token: data.request_token });
        infoViewActionsContext.showMessage(data.message);
      })
      .catch((error: any) => {
        onRequestAccess();
        // infoViewActionsContext.showError(error.message);
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
