import {Fragment} from 'react';
import {Button, Space} from 'antd';
import type {TooltipPlacement} from 'antd/es/tooltip';
import {ACCESS_ROLE} from '@unpod/constants/AppEnums';
import {
  deleteDataApi,
  getDataApi,
  postDataApi,
  useAuthActionsContext,
  useAuthContext,
  useInfoViewActionsContext,
} from '@unpod/providers';
import {AppPopover} from '../../antd';
import {useRouter} from 'next/navigation';

type RequestEntityType = 'org' | 'space' | 'thread' | string;

type RequestEntityData = {
  domain_handle?: string;
  slug?: string;
  privacy_type?: 'public' | 'shared' | string;
  final_role?: string;
  request_token?: string | null;
  is_requested?: boolean;
  [key: string]: any;
};

const getJoinEntityUrl = (
  type: RequestEntityType,
  currentData: RequestEntityData,
) => {
  switch (type) {
    case 'org':
      return `organization/subscribe/join/${currentData.domain_handle}/`;
    case 'space':
      return `spaces/subscribe/join/${currentData.slug}/`;
    default:
      return `threads/${currentData?.slug}/subscribe/`;
  }
};

const getLeaveEntityUrl = (
  type: RequestEntityType,
  currentData: RequestEntityData,
) => {
  switch (type) {
    case 'org':
      return `organization/subscribe/leave/${currentData.domain_handle}/`;
    case 'space':
      return `spaces/subscribe/leave/${currentData.slug}/`;
    default:
      return `threads/${currentData?.slug}/unsubscribe/`;
  }
};

const getEntityRequestUrl = (
  type: RequestEntityType,
  currentData: RequestEntityData,
) => {
  switch (type) {
    case 'org':
      return `organization/${currentData.domain_handle}/request/`;
    case 'space':
      return `spaces/${currentData.slug}/request/`;
    default:
      return `threads/${currentData?.slug}/subscribe/`;
  }
};

const getEntityEditRequestUrl = (
  type: RequestEntityType,
  currentData: RequestEntityData,
) => {
  switch (type) {
    case 'org':
      return `organization/${currentData.domain_handle}/request/change-role/`;
    case 'space':
      return `spaces/${currentData.slug}/request/change-role/`;
    default:
      return `threads/${currentData?.slug}/subscribe/${currentData?.request_token}/`;
  }
};

const getEntityResendRequestUrl = (
  type: RequestEntityType,
  currentData: RequestEntityData,
) => {
  switch (type) {
    case 'org':
      return `organization/${currentData.domain_handle}/request/${currentData.request_token}/resend/`;
    case 'space':
      return `spaces/${currentData.slug}/request/${currentData.request_token}/resend/`;
    default:
      return `threads/${currentData?.slug}/request/${currentData?.request_token}/resend/`;
  }
};

const getButtonTitle = (
  currentData: RequestEntityData,
  type: RequestEntityType,
) => {
  switch (type) {
    case 'org':
      return currentData?.domain_handle && currentData.privacy_type === 'public'
        ? 'Join'
        : 'Subscribe';
    case 'space':
      return currentData?.slug && currentData.privacy_type === 'public'
        ? 'Join'
        : 'Subscribe';
    default:
      return currentData?.slug && currentData.privacy_type === 'public'
        ? 'Join'
        : 'Subscribe';
  }
};

type RequestPopoverProps = {
  type: RequestEntityType;
  placement?: TooltipPlacement;
  title?: string;
  linkShareable?: boolean;
  userList?: unknown[];
  currentData: RequestEntityData;
  setCurrentData: (data: RequestEntityData) => void;
  [key: string]: unknown;
};

const RequestPopover = ({
                          type,
                          placement = 'bottomRight',
                          title = 'Share your thread!',
                          linkShareable = false,
                          userList = [],
                          currentData,
                          setCurrentData,
                          ...restProps
                        }: RequestPopoverProps) => {
  console.log('RequestPopover currentData', currentData);
  const infoViewActionsContext = useInfoViewActionsContext();
  const {setActiveOrg, updateAuthUser} = useAuthActionsContext();
  const {user} = useAuthContext();
  const router = useRouter();
  const onUpdate = (data: RequestEntityData) => {
    setCurrentData({...currentData, ...data});
  };

  const onJoinEntity = () => {
    const url = getJoinEntityUrl(type, currentData);
    getDataApi(url, infoViewActionsContext)
      .then((data: any) => {
        onUpdate(data.data);
        infoViewActionsContext.showMessage(data.message);
      })
      .catch((error: any) => {
        infoViewActionsContext.showError(error.message);
      });
  };

  const onEntityRequest = () => {
    const url = getEntityRequestUrl(type, currentData);
    getDataApi(url, infoViewActionsContext)
      .then((data: any) => {
        onUpdate({
          ...data.data,
          request_token: data?.data?.request_token,
          is_requested: true,
        });
        infoViewActionsContext.showMessage(data.message);
      })
      .catch((error: any) => {
        infoViewActionsContext.showError(error.message);
      });
  };

  const onEntityEditRequest = () => {
    const url = getEntityEditRequestUrl(type, currentData);
    postDataApi(url, infoViewActionsContext, {
      role_code: ACCESS_ROLE.EDITOR,
    })
      .then((data: any) => {
        onUpdate({
          ...data.data,
          request_token: data?.data?.request_token,
          is_requested: true,
        });
        infoViewActionsContext.showMessage(data.message);
      })
      .catch((error: any) => {
        infoViewActionsContext.showError(error.message);
      });
  };

  const onEntityResendRequest = () => {
    const url = getEntityResendRequestUrl(type, currentData);
    getDataApi(url, infoViewActionsContext)
      .then((data: any) => {
        onUpdate({
          ...data.data,
          request_token: data?.data?.request_token,
          is_requested: true,
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
        : type === 'space'
          ? `spaces/${currentData.slug}/request/${currentData.request_token}/`
          : `threads/${currentData?.slug}/request/${currentData?.request_token}/`;

    deleteDataApi(url, infoViewActionsContext)
      .then((data: any) => {
        onUpdate({
          ...data.data,
          request_token: null,
          is_requested: false,
        });
        infoViewActionsContext.showMessage(data.message);
      })
      .catch((error: any) => {
        infoViewActionsContext.showError(error.message);
      });
  };

  const onLeaveEntity = () => {
    const url = getLeaveEntityUrl(type, currentData);
    getDataApi(url, infoViewActionsContext)
      .then((data: any) => {
        if (type === 'org') {
          if (!user) {
            infoViewActionsContext.showError('User not available.');
            return;
          }
          const organizationList = (user.organization_list ?? []).filter(
            (org: any) => org.domain_handle !== currentData.domain_handle,
          );
          if (organizationList.length > 0) {
            setActiveOrg(organizationList[0] || null);
          } else {
            setActiveOrg(null);
            // router.push('/create-org');
            if (user?.is_private_domain) {
              router.push('/creating-identity/');
            } else {
              router.push('/business-identity/');
            }
          }
          updateAuthUser({
            ...user,
            organization_list: organizationList,
          });
        } else {
          onUpdate({...data.data, final_role: ACCESS_ROLE.GUEST});
        }

        infoViewActionsContext.showMessage(data.message);
      })
      .catch((error: any) => {
        infoViewActionsContext.showError(error.message);
      });
  };

  const isLeaveAllowed = () => {
    if (currentData) {
      return (
        currentData?.final_role && currentData?.final_role !== ACCESS_ROLE.GUEST
      );
    }
    return false;
  };

  const isJoinAllowed = () => {
    if (currentData && currentData?.privacy_type === 'public') {
      return (
        (currentData?.final_role === ACCESS_ROLE.GUEST ||
          !currentData?.final_role) &&
        !currentData?.is_requested
      );
    }
    return false;
  };
  const isRequestAllowed = () => {
    if (
      currentData &&
      currentData?.privacy_type === 'shared' &&
      !currentData?.is_requested
    ) {
      return currentData?.final_role === ACCESS_ROLE.GUEST;
    }
    return false;
  };

  const isEditRequestAllowed = () => {
    if (
      currentData &&
      (currentData?.privacy_type === 'shared' ||
        currentData?.privacy_type === 'public')
    ) {
      return currentData?.final_role === ACCESS_ROLE.VIEWER;
    }
    return false;
  };

  const isSharedRequested = () => {
    if (currentData && currentData?.privacy_type === 'shared') {
      return (
        currentData?.is_requested &&
        currentData?.final_role !== ACCESS_ROLE.VIEWER
      );
    }
    return false;
  };

  const getPrivacyType = () => {
    if (currentData && currentData?.privacy_type) {
      return currentData?.privacy_type;
    }
    return false;
  };

  return (
    <AppPopover
      content={
        <Space orientation="vertical">
          {isJoinAllowed() ? (
            <Button
              type="primary"
              style={{
                width: 150,
              }}
              onClick={() => {
                if (getPrivacyType() === 'shared') {
                  onEntityRequest();
                } else {
                  onJoinEntity();
                }
              }}
            >
              {getButtonTitle(currentData, type)}
            </Button>
          ) : null}

          {isRequestAllowed() ? (
            <Button
              type="primary"
              style={{
                width: 150,
              }}
              onClick={onEntityRequest}
            >
              Request
            </Button>
          ) : null}
          {isEditRequestAllowed() ? (
            <Button
              type="primary"
              style={{
                minWidth: 150,
              }}
              disabled={
                currentData?.is_requested &&
                currentData?.final_role === ACCESS_ROLE.VIEWER
              }
              onClick={onEntityEditRequest}
            >
              {currentData?.is_requested &&
              currentData?.final_role === ACCESS_ROLE.VIEWER
                ? 'Requested Editor Access'
                : 'Request Editor Access'}
            </Button>
          ) : null}

          {isSharedRequested() ? (
            <Fragment>
              <Button
                type="primary"
                style={{
                  width: 150,
                }}
                onClick={onEntityResendRequest}
              >
                Resend Request
              </Button>

              <Button
                type="primary"
                style={{
                  width: 150,
                }}
                onClick={onDeleteRequest}
                danger
              >
                Delete Request
              </Button>
            </Fragment>
          ) : null}

          {isLeaveAllowed() ? (
            <Button
              danger
              style={{
                width: 150,
              }}
              onClick={onLeaveEntity}
            >
              Leave
            </Button>
          ) : null}
        </Space>
      }
      placement={placement}
      {...restProps}
    />
  );
};

export default RequestPopover;
