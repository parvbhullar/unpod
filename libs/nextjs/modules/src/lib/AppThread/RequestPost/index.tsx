import { useEffect, useState } from 'react';
import { StyledPlaceHolder, StyledPlaceHolderInner } from './index.styled';
import AppImage from '@unpod/components/next/AppImage';
import { Button, Space, Typography } from 'antd';
import { getDataApi, useInfoViewActionsContext } from '@unpod/providers';
import { useIntl } from 'react-intl';

type RequestPostProps = {
  post: any;
};

const RequestPost = ({ post }: RequestPostProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const [myPost, setMyPost] = useState<any>(post);
  const { formatMessage } = useIntl();

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
          {formatMessage({ id: 'hub.noPostAccess' })}
        </Typography.Title>

        <Space>
          {myPost?.is_requested ? (
            <>
              {/* <Button type="primary" onClick={onDeleteRequest}>
                Delete Request
              </Button>*/}
              <Button type="primary" onClick={onResendRequest}>
                {formatMessage({ id: 'request.resendRequest' })}
              </Button>
            </>
          ) : (
            <Button type="primary" onClick={onRequestAccess}>
              {formatMessage({ id: 'request.requestAccess' })}
            </Button>
          )}
        </Space>
      </StyledPlaceHolderInner>
    </StyledPlaceHolder>
  );
};

export default RequestPost;
