'use client';

import {useEffect, useMemo, useState} from 'react';
import type {MenuProps} from 'antd';
import {Button, Dropdown, Row, Space, Typography} from 'antd';
import {RiArrowDownSFill} from 'react-icons/ri';
import {useRouter} from 'next/navigation';
import {useIntl} from 'react-intl';

import {StyledSpace} from './index.styled';
import {getSharedOptions} from './data';
import InviteUserSection from './InviteUserSection';
import InvitedUsersList from './InvitedUsersList';
import RequestedUsersList from './RequestedUsersList';
import type {PermissionEntity, PermissionMember, PermissionPopoverProps, PermissionPopoverType,} from './types';

import {
  getDataApi,
  putDataApi,
  uploadPutDataApi,
  useAuthActionsContext,
  useAuthContext,
  useInfoViewActionsContext,
} from '@unpod/providers';
import {SITE_URL} from '@unpod/constants';
import {ACCESS_ROLE} from '@unpod/constants/AppEnums';
import type {EntityWithOperations} from '@unpod/helpers/PermissionHelper';
import {isEditAccessAllowed, isPrivacyUpdateAllow, isShareAccessAllowed,} from '@unpod/helpers/PermissionHelper';
import type {Organization} from '@unpod/constants/types';

import {AppPopover} from '../../antd';
import AppCopyToClipboard from '../../third-party/AppCopyToClipboard';

const toErrorMessage = (error: unknown): string => {
  if (error && typeof error === 'object' && 'message' in error) {
    const message = (error as { message?: unknown }).message;
    if (typeof message === 'string') return message;
  }
  return 'Something went wrong';
};

const getTitle = (type: PermissionPopoverType): string => {
  switch (type) {
    case 'org':
      return 'permissionPopover.orgTitle';
    case 'space':
      return 'permissionPopover.spaceTitle';
    case 'note':
      return 'permissionPopover.noteTitle';
    case 'chat':
      return 'permissionPopover.chatTitle';
    case 'doc':
      return 'permissionPopover.docTitle';
    default:
      return 'permissionPopover.defaultTitle';
  }
};

const getLeaveUrl = (
  type: PermissionPopoverType,
  currentData?: PermissionEntity | null,
): string => {
  switch (type) {
    case 'org':
      return `organization/subscribe/leave/${currentData?.domain_handle || ''}/`;
    case 'space':
      return `spaces/subscribe/leave/${currentData?.slug || ''}/`;
    default:
      return `threads/${currentData?.slug || ''}/unsubscribe/`;
  }
};

const getShareTypeUrl = (
  type: PermissionPopoverType,
  currentData?: PermissionEntity | null,
): string => {
  switch (type) {
    case 'org':
      return `organization/${currentData?.domain_handle || ''}/`;
    case 'space':
      return `spaces/${currentData?.slug || ''}/`;
    default:
      return `threads/${currentData?.slug || ''}/action/`;
  }
};

const getLinkText = (
  type: PermissionPopoverType,
  currentData?: PermissionEntity | null,
): string => {
  switch (type) {
    case 'org':
      return `${SITE_URL}/${currentData?.domain_handle ? `${currentData.domain_handle}/org` : ''}`;
    case 'space':
      return `${SITE_URL}/${currentData?.slug ? `spaces/${currentData.slug}/` : ''}`;
    default:
      return `${SITE_URL}/${currentData?.slug ? `thread/${currentData.slug}/` : ''}`;
  }
};

const isLeaveAccessAllowed = (
  currentData?: PermissionEntity | null,
): boolean => {
  return currentData?.final_role === ACCESS_ROLE.EDITOR;
};

const getPermissionScope = (
  type: PermissionPopoverType,
  currentData?: PermissionEntity | null,
): [
    EntityWithOperations | undefined,
    EntityWithOperations | undefined,
    EntityWithOperations | undefined,
] => {
  if (!currentData) return [undefined, undefined, undefined];
  if (type === 'org') return [currentData, undefined, undefined];
  if (type === 'space') return [undefined, undefined, currentData];
  return [undefined, currentData, undefined];
};

const getPopupContainer = (triggerNode: HTMLElement): HTMLElement => {
  return triggerNode.parentElement ?? triggerNode;
};

const PermissionPopover = ({
                             type = 'org',
                             title = 'modal.shareSpace',
                             placement = 'bottomRight',
                             linkShareable = false,
                             currentData,
                             setCurrentData,
                             userList: _userList,
                             setUserList: _setUserList,
                             ...restProps
                           }: PermissionPopoverProps) => {
  const {setActiveOrg, updateAuthUser} = useAuthActionsContext();
  const {user} = useAuthContext();
  const {formatMessage} = useIntl();
  const router = useRouter();
  const infoViewActionsContext = useInfoViewActionsContext();

  const [userList, setUserList] = useState<PermissionMember[]>([]);
  const [shareType, setShareType] = useState<string>(
    currentData?.privacy_type || 'private',
  );

  const sharedOptions = useMemo(() => getSharedOptions(type), [type]);

  const selectedShareType = useMemo(() => {
    return sharedOptions.find((item) => item.key === shareType) || null;
  }, [shareType, sharedOptions]);

  const dropdownItems = useMemo<MenuProps['items']>(() => {
    return sharedOptions.map((item) => ({
      key: item.key,
      label: formatMessage({id: item.label}),
    }));
  }, [sharedOptions, formatMessage]);

  const [currentHub, currentPost, currentSpace] = useMemo(
    () => getPermissionScope(type, currentData),
    [type, currentData],
  );

  useEffect(() => {
    if (currentData?.users) {
      const existingUsers = currentData.users as PermissionMember[];
      setUserList(
        existingUsers.map((item) => ({
          ...item,
          email: item.email || item.user_email,
          role_code: item.role_code || item.role,
        })),
      );
      return;
    }
    setUserList([]);
  }, [currentData?.users]);

  useEffect(() => {
    setShareType(currentData?.privacy_type || 'private');
  }, [currentData]);

  const onRemoveInvitedMember = (email: string): void => {
    const newMembers = userList.filter((item) => item.email !== email);
    setUserList(newMembers);
    setCurrentData({
      ...(currentData || {}),
      users: newMembers,
    });
  };

  const onUpdateInvitedMember = (member: PermissionMember): void => {
    let members = userList.map((item) =>
      item.email === member.email ? member : item,
    );

    if (
      member.role_code === ACCESS_ROLE.OWNER &&
      (type === 'org' || type === 'space')
    ) {
      members = members.map((item) =>
        item.email === user?.email
          ? {
            ...item,
            role_code: ACCESS_ROLE.EDITOR,
            role: ACCESS_ROLE.EDITOR,
          }
          : item,
      );
    }

    setUserList(members);
    setCurrentData({
      ...(currentData || {}),
      users: members,
    });
  };

  const onChangeShareType: MenuProps['onClick'] = (item) => {
    const nextShareType = String(item.key);
    const url = getShareTypeUrl(type, currentData);

    if (type === 'org') {
      const formData = new FormData();
      formData.append('privacy_type', nextShareType);
      setShareType(nextShareType);

      uploadPutDataApi<Organization>(url, infoViewActionsContext, formData)
        .then((response) => {
          setShareType(nextShareType);
          infoViewActionsContext.showMessage(response.message || 'Updated');

          const mergedData = {
            ...(currentData || {}),
            ...response.data,
          } as PermissionEntity;

          setCurrentData(mergedData);

          if (user) {
            const organizationList = (user.organization_list || []).map(
              (org) =>
                org.domain_handle === response.data.domain_handle
                  ? response.data
                  : org,
            );

            updateAuthUser({
              ...user,
              active_organization: response.data,
              organization_list: organizationList,
            });
          }
        })
        .catch((error: unknown) => {
          infoViewActionsContext.showError(toErrorMessage(error));
        });
      return;
    }

    putDataApi<PermissionEntity>(url, infoViewActionsContext, {
      privacy_type: nextShareType,
    })
      .then((response) => {
        setShareType(nextShareType);
        setCurrentData({
          ...(currentData || {}),
          privacy_type: nextShareType,
        });
        infoViewActionsContext.showMessage(response.message || 'Updated');
      })
      .catch((error: unknown) => {
        infoViewActionsContext.showError(toErrorMessage(error));
      });
  };

  const onUpdate = (data: Partial<PermissionEntity>): void => {
    setCurrentData({...(currentData || {}), ...data});
  };

  const onLeaveEntity = (): void => {
    const url = getLeaveUrl(type, currentData);

    getDataApi<PermissionEntity>(url, infoViewActionsContext)
      .then((response) => {
        if (type === 'org' && user) {
          const organizationList = (user.organization_list || []).filter(
            (org) => org.domain_handle !== currentData?.domain_handle,
          );

          if (organizationList.length > 0) {
            setActiveOrg(organizationList[0] || null);
          } else {
            setActiveOrg(null);
            if (user.is_private_domain) {
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
          onUpdate({...(response.data || {}), final_role: ACCESS_ROLE.GUEST});
        }

        infoViewActionsContext.showMessage(response.message || 'Updated');
      })
      .catch((error: unknown) => {
        infoViewActionsContext.showError(toErrorMessage(error));
      });
  };

  const canShareAccess = isShareAccessAllowed(
    currentHub,
    currentPost,
    currentSpace,
  );
  const canEditAccess = isEditAccessAllowed(
    currentHub,
    currentPost,
    currentSpace,
  );
  const canPrivacyUpdate = isPrivacyUpdateAllow(
    currentHub,
    currentPost,
    currentSpace,
  );

  return (
    <AppPopover
      content={
        <div
          style={{
            minWidth: 500,
          }}
        >
          {canShareAccess ? (
            <>
              <RequestedUsersList
                type={type}
                userList={userList}
                setUserList={setUserList}
                currentData={currentData}
                setCurrentData={setCurrentData}
              />
              <InviteUserSection
                type={type}
                userList={userList}
                setUserList={setUserList}
                currentData={currentData}
                setCurrentData={setCurrentData}
              />
            </>
          ) : null}

          {canEditAccess ? (
            <InvitedUsersList
              type={type}
              currentData={currentData}
              userList={userList}
              onRemoveInvitedMember={onRemoveInvitedMember}
              onUpdateInvitedMember={onUpdateInvitedMember}
            />
          ) : null}

          {linkShareable && canPrivacyUpdate ? (
            <Dropdown
              menu={{
                items: dropdownItems,
                onClick: onChangeShareType,
              }}
              trigger={['click']}
              getPopupContainer={getPopupContainer}
            >
              <div>
                <StyledSpace>
                  <span>{selectedShareType?.image}</span>
                  <div>
                    <Space>
                      <Typography.Text strong>
                        {selectedShareType
                          ? formatMessage({id: selectedShareType.label})
                          : formatMessage({id: 'permissionPopover.private'})}
                      </Typography.Text>
                      <RiArrowDownSFill fontSize={24}/>
                    </Space>
                    <Typography.Paragraph className={'mb-0'}>
                      {selectedShareType
                        ? formatMessage({id: selectedShareType.description})
                        : formatMessage({
                          id: 'permissionPopover.privateDescription',
                        })}
                    </Typography.Paragraph>
                  </div>
                </StyledSpace>
              </div>
            </Dropdown>
          ) : canPrivacyUpdate ? (
            <StyledSpace>
              <span>{selectedShareType?.image}</span>
              <div>
                <Space>
                  <Typography.Text strong>
                    {selectedShareType
                      ? formatMessage({id: selectedShareType.label})
                      : formatMessage({id: 'permissionPopover.private'})}
                  </Typography.Text>
                </Space>
                <Typography.Paragraph className={'mb-0'}>
                  {selectedShareType
                    ? formatMessage({id: selectedShareType.description})
                    : formatMessage({
                      id: 'permissionPopover.privateDescription',
                    })}
                </Typography.Paragraph>
              </div>
            </StyledSpace>
          ) : null}

          {shareType !== 'private' ? (
            <Row justify="end">
              <Space size="large">
                {isLeaveAccessAllowed(currentData) ? (
                  <Button danger size="small" onClick={onLeaveEntity}>
                    {formatMessage({id: 'permissionPopover.leave'})}
                  </Button>
                ) : null}
                <AppCopyToClipboard text={getLinkText(type, currentData)}/>
              </Space>
            </Row>
          ) : null}
        </div>
      }
      title={
        <Row justify="space-between" align="middle">
          <Typography.Text>
            {title
              ? title.includes('.')
                ? formatMessage({id: title})
                : title
              : formatMessage({id: getTitle(type)})}
          </Typography.Text>
        </Row>
      }
      placement={placement}
      showArrow={false}
      {...restProps}
    />
  );
};

export default PermissionPopover;
