import AppImage from '@unpod/components/next/AppImage';
import { Button, Space, Typography } from 'antd';
import {
  deleteDataApi,
  getDataApi,
  useInfoViewActionsContext,
} from '@unpod/providers';
import { StyledPlaceHolder, StyledPlaceHolderInner } from './index.styled';
import { useIntl } from 'react-intl';

const RequestWorkSpace = ({
  currentData,
  setCurrentData,
  type = 'space',
}: {
  currentData: any;
  setCurrentData: (data: any) => void;
  type?: 'space' | 'org' | 'post' | string;
}) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const { formatMessage } = useIntl();

  const onAccessRequest = () => {
    const url =
      type === 'org'
        ? `organization/${currentData.domain_handle}/request/`
        : `spaces/${currentData.slug}/request/`;

    getDataApi(url, infoViewActionsContext)
      .then((data: any) => {
        setCurrentData({
          ...currentData,
          request_token: data.data.request_token,
          is_requested: true,
        });
        infoViewActionsContext.showMessage(data.message);
      })
      .catch((error: any) => {
        infoViewActionsContext.showError(error.message);
      });
  };

  const onJoinRequest = () => {
    const url =
      type === 'org'
        ? `organization/subscribe/join/${currentData.domain_handle}/`
        : `spaces/subscribe/join/${currentData.slug}/`;

    getDataApi(url, infoViewActionsContext)
      .then((data: any) => {
        setCurrentData({
          ...currentData,
          ...data.data,
        });
        infoViewActionsContext.showMessage(data.message);
      })
      .catch((error: any) => {
        infoViewActionsContext.showError(error.message);
      });
  };
  const onDeleteRequest = () => {
    const url =
      type === 'org'
        ? `organization/${currentData.domain_handle}/request/${currentData.request_token}/`
        : `spaces/${currentData.slug}/request/${currentData.request_token}/`;

    deleteDataApi(url, infoViewActionsContext)
      .then((data: any) => {
        setCurrentData({
          ...currentData,
          request_token: null,
          is_requested: false,
        });
        infoViewActionsContext.showMessage(data.message);
      })
      .catch((error: any) => {
        console.log(error);
      });
  };

  const onResendRequest = () => {
    const url =
      type === 'org'
        ? `organization/${currentData.domain_handle}/request/${currentData.request_token}/resend/`
        : `spaces/${currentData.slug}/request/${currentData.request_token}/resend/`;

    getDataApi(url, infoViewActionsContext)
      .then((data: any) => {
        setCurrentData({
          ...currentData,
          request_token: data?.data?.request_token,
        });
        infoViewActionsContext.showMessage(data.message);
      })
      .catch((error: any) => {
        infoViewActionsContext.showError(error.message);
      });
  };

  const getAccessText = () => {
    if (type === 'org') {
      return formatMessage({ id: 'request.noAccessOrg' });
    } else if (type === 'space') {
      return formatMessage({ id: 'request.noAccessSpace' });
    } else {
      return formatMessage({ id: 'request.noAccessPost' });
    }
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
          {getAccessText()}
        </Typography.Title>

        {currentData?.privacy_type === 'shared' &&
        currentData?.final_role === 'guest' ? (
          <Space>
            {currentData?.is_requested ? (
              <>
                <Button type="primary" danger onClick={onDeleteRequest}>
                  {formatMessage({ id: 'request.resendDelete' })}
                </Button>
                <Button type="primary" onClick={onResendRequest}>
                  {formatMessage({ id: 'request.resendRequest' })}
                </Button>
              </>
            ) : (
              <Button type="primary" onClick={onAccessRequest}>
                {formatMessage({ id: 'request.requestAccess' })}
              </Button>
            )}
          </Space>
        ) : currentData?.privacy_type === 'shared' &&
          currentData?.final_role === 'guest' ? (
          <Button type="primary" onClick={onJoinRequest}>
            {formatMessage({ id: 'common.join' })}
          </Button>
        ) : null}
      </StyledPlaceHolderInner>
    </StyledPlaceHolder>
  );
};

export default RequestWorkSpace;
