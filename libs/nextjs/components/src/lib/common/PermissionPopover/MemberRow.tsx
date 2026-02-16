'use client';

import { useMemo, useState } from 'react';
import {
  Button,
  Dropdown,
  Popconfirm,
  Row,
  Space,
  Typography,
} from 'antd';
import type { MenuProps } from 'antd';
import { RiArrowDownSFill } from 'react-icons/ri';
import { useIntl } from 'react-intl';

import UserAvatar from '../UserAvatar';
import type {
  GlobalRoleMap,
  MemberRowProps,
  PermissionEntity,
  PermissionPopoverType,
  RoleRecord,
} from './types';

import {
  deleteDataApi,
  getDataApi,
  putDataApi,
  useAuthContext,
  useInfoViewActionsContext,
} from '@unpod/providers';
import { ACCESS_ROLE } from '@unpod/constants/AppEnums';
import {
  getSpaceAllowedRoles,
  isEditAccessAllowed,
  isTransferOwnershipAllowed,
} from '@unpod/helpers/PermissionHelper';
import type { EntityWithOperations } from '@unpod/helpers/PermissionHelper';
import { maskEmail } from '@unpod/helpers/StringHelper';
import { getRoleLabel } from '@unpod/helpers/LocalizationFormatHelper';

const getRoleChangeURL = (
  type: PermissionPopoverType,
  currentData: PermissionEntity | null | undefined,
  memberEmail: string,
): string => {
  switch (type) {
    case 'org':
      return `organization/invite/resend/${memberEmail}/`;
    case 'space':
      return `spaces/invite/resend/${currentData?.invite_token || ''}/`;
    default:
      return '';
  }
};

const getOwnerChangeURL = (
  type: PermissionPopoverType,
  currentData: PermissionEntity | null | undefined,
): string => {
  switch (type) {
    case 'org':
      return `organization/ownership-transfer/${currentData?.domain_handle || ''}/`;
    case 'space':
      return `spaces/${currentData?.token || ''}/ownership-transfer/`;
    default:
      return '';
  }
};

const getRemoveAccessURL = (
  type: PermissionPopoverType,
  currentData: PermissionEntity | null | undefined,
  memberEmail: string,
): string => {
  switch (type) {
    case 'org':
      return `organization/permission/${currentData?.domain_handle || ''}/?email=${memberEmail}`;
    case 'space':
      return `spaces/${currentData?.token || ''}/permission/?email=${memberEmail}`;
    default:
      return `threads/${currentData?.slug || ''}/permission/?email=${memberEmail}`;
  }
};

const getRemoveInviteURL = (
  type: PermissionPopoverType,
  currentData: PermissionEntity | null | undefined,
  member: MemberRowProps['member'],
): string => {
  switch (type) {
    case 'org':
      return `organization/invite/${member.invite_token || ''}/?email=${member.email || ''}`;
    case 'space':
      return `spaces/invite/${member.invite_token || ''}/`;
    default:
      return `threads/${currentData?.slug || ''}/permission/?email=${member.email || ''}`;
  }
};

const getUpdatePermissionURL = (
  type: PermissionPopoverType,
  currentData: PermissionEntity | null | undefined,
): string => {
  switch (type) {
    case 'org':
      return `organization/permission/${currentData?.domain_handle || ''}/`;
    case 'space':
      return `spaces/${currentData?.token || ''}/permission/`;
    default:
      return `threads/${currentData?.slug || ''}/permission/`;
  }
};

const getEntityName = (
  type: PermissionPopoverType,
  currentData: PermissionEntity | null | undefined,
): string => {
  switch (type) {
    case 'org':
      return String(currentData?.name || '');
    case 'space':
      return String(currentData?.name || '');
    default:
      return String(currentData?.title || '');
  }
};

const toErrorMessage = (error: unknown): string => {
  if (error && typeof error === 'object' && 'message' in error) {
    const message = (error as { message?: unknown }).message;
    if (typeof message === 'string') return message;
  }
  return 'Something went wrong';
};

const getPermissionScope = (
  type: PermissionPopoverType,
  currentData: PermissionEntity | null | undefined,
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

const MemberRow = ({
  type,
  member,
  currentData,
  onRemoveInvitedMember,
  onUpdateInvitedMember,
}: MemberRowProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const { user, globalData } = useAuthContext();
  const { formatMessage } = useIntl();

  const [roleCode, setRoleCode] = useState<string>('');

  const roles = (globalData.roles as GlobalRoleMap) || {};
  const memberEmail = member.email || member.user_email || '';

  const [currentHub, currentPost, currentSpace] = useMemo(
    () => getPermissionScope(type, currentData),
    [type, currentData],
  );

  const transferOwnership = (): void => {
    const url = getOwnerChangeURL(type, currentData);
    if (!url) return;

    getDataApi(url, infoViewActionsContext, {
      email: memberEmail,
    })
      .then((response) => {
        infoViewActionsContext.showMessage(response.message || 'Updated');
        onUpdateInvitedMember({
          ...member,
          role_code: ACCESS_ROLE.OWNER,
          role: ACCESS_ROLE.OWNER,
        });
      })
      .catch((error: unknown) => {
        infoViewActionsContext.showError(toErrorMessage(error));
      });
  };

  const removeInvite = (): void => {
    const url = getRemoveInviteURL(type, currentData, member);
    if (!url) return;

    deleteDataApi(url, infoViewActionsContext)
      .then((response) => {
        infoViewActionsContext.showMessage(response.message || 'Updated');
        onRemoveInvitedMember(memberEmail);
      })
      .catch((error: unknown) => {
        infoViewActionsContext.showError(toErrorMessage(error));
      });
  };

  const removeAccess = (): void => {
    const url = getRemoveAccessURL(type, currentData, memberEmail);
    if (!url) return;

    deleteDataApi(url, infoViewActionsContext)
      .then((response) => {
        infoViewActionsContext.showMessage(response.message || 'Updated');
        onRemoveInvitedMember(memberEmail);
      })
      .catch((error: unknown) => {
        infoViewActionsContext.showError(toErrorMessage(error));
      });
  };

  const onUpdatePermission = (nextRoleCode: string): void => {
    const url = getUpdatePermissionURL(type, currentData);
    if (!url) return;

    putDataApi(url, infoViewActionsContext, {
      email: memberEmail,
      role_code: nextRoleCode,
    })
      .then((response) => {
        infoViewActionsContext.showMessage(response.message || 'Updated');
        onUpdateInvitedMember({
          ...member,
          role_code: nextRoleCode,
          role: nextRoleCode,
        });
      })
      .catch((error: unknown) => {
        infoViewActionsContext.showError(toErrorMessage(error));
      });
  };

  const onConfirmClick = (nextRoleCode: string): void => {
    setRoleCode('');

    if (nextRoleCode === ACCESS_ROLE.OWNER) {
      transferOwnership();
      return;
    }
    if (nextRoleCode === 'remove-access') {
      removeAccess();
      return;
    }
    if (nextRoleCode === 'remove-invite') {
      removeInvite();
    }
  };

  const onRoleChange: MenuProps['onClick'] = (item) => {
    const nextKey = String(item.key);

    if (
      nextKey === ACCESS_ROLE.OWNER ||
      nextKey === 'remove-access' ||
      nextKey === 'remove-invite'
    ) {
      setRoleCode(nextKey);
      return;
    }

    if (nextKey === 'resend-invite') {
      const url = getRoleChangeURL(type, currentData, memberEmail);
      if (!url) return;

      getDataApi(url, infoViewActionsContext)
        .then((response) => {
          infoViewActionsContext.showMessage(response.message || 'Updated');
        })
        .catch((error: unknown) => {
          infoViewActionsContext.showError(toErrorMessage(error));
        });
      return;
    }

    if (nextKey !== 'divider') {
      onUpdatePermission(nextKey);
    }
  };

  const getRoleList = (): MenuProps['items'] => {
    const roleData = (type === 'space' ? roles.space : roles.post || []) as
      | RoleRecord[]
      | undefined;
    const userRoles = currentData?.users || [];

    const canTransferOwnership = isTransferOwnershipAllowed(
      currentHub,
      currentPost,
      currentSpace,
    );
    const canEdit = isEditAccessAllowed(currentHub, currentPost, currentSpace);

    const roleList: NonNullable<MenuProps['items']> = getSpaceAllowedRoles(
      roleData || [],
      userRoles,
      user,
    )
      .filter((item) => !!item.role_code)
      .map((item) => {
        const code = item.role_code || ACCESS_ROLE.VIEWER;
        return {
          key: code,
          label: getRoleLabel(code, formatMessage),
          disabled:
            code === ACCESS_ROLE.OWNER
              ? !canTransferOwnership || !member.joined
              : !canEdit,
        };
      });

    if (roleList.length > 1 || !member.joined) {
      roleList.push({ type: 'divider' });
    }

    if (!member.joined) {
      roleList.push({
        key: 'resend-invite',
        label: formatMessage({ id: 'member.resendInvite' }),
      });
      roleList.push({
        key: 'remove-invite',
        label: formatMessage({ id: 'member.removeInvite' }),
        danger: true,
      });
    }

    if (member.joined) {
      roleList.push({
        key: 'remove-access',
        label: formatMessage({ id: 'member.removeAccess' }),
        danger: true,
      });
    }

    return roleList;
  };

  const { title, content, okText } = useMemo(() => {
    const name = member.full_name || memberEmail;
    const entityName = getEntityName(type, currentData);

    const contentText =
      roleCode === ACCESS_ROLE.OWNER
        ? formatMessage(
            { id: 'member.confirmOwnership' },
            { name, entity: entityName },
          )
        : member.joined
          ? formatMessage(
              { id: 'member.confirmRemoveAccess' },
              { name, entity: entityName },
            )
          : formatMessage({ id: 'member.confirmRemoveInvite' });

    const titleText =
      roleCode === ACCESS_ROLE.OWNER
        ? formatMessage({ id: 'member.transferOwnership' })
        : member.joined
          ? formatMessage({ id: 'member.removeAccessTitle' })
          : formatMessage({ id: 'member.removeInviteTitle' });

    return {
      title: titleText,
      content: contentText,
      okText: titleText,
    };
  }, [currentData, formatMessage, member, memberEmail, roleCode, type]);

  return (
    <Row justify="space-between" align="middle">
      <Space>
        <UserAvatar user={member} />
        <Space orientation="vertical" size={0}>
          {member.full_name ? (
            <Typography.Text
              type={member.joined ? undefined : 'secondary'}
              style={{ marginBottom: -4, display: 'block' }}
            >
              {member.full_name}{' '}
              {memberEmail === user?.email ? (
                <strong>{formatMessage({ id: 'member.you' })}</strong>
              ) : null}
            </Typography.Text>
          ) : null}

          <Typography.Text type={member.joined ? undefined : 'secondary'}>
            {maskEmail(memberEmail)}
          </Typography.Text>

          {member.joined ? null : (
            <Typography.Text>{formatMessage({ id: 'member.invited' })}</Typography.Text>
          )}
        </Space>
      </Space>

      {member.role === ACCESS_ROLE.OWNER ? (
        <Typography.Text style={{ marginRight: 24 }}>
          {formatMessage({ id: 'member.owner' })}
        </Typography.Text>
      ) : (
        <Popconfirm
          arrow={false}
          title={title}
          open={roleCode !== ''}
          onConfirm={() => onConfirmClick(roleCode)}
          onCancel={() => setRoleCode('')}
          description={content}
          okText={okText}
          cancelText={formatMessage({ id: 'common.cancel' })}
        >
          <Dropdown
            menu={{
              items: getRoleList(),
              onClick: onRoleChange,
              selectedKeys: [member.role || ACCESS_ROLE.VIEWER],
            }}
            trigger={['click']}
          >
            <Button>
              <Space>
                {getRoleLabel(member.role || ACCESS_ROLE.VIEWER, formatMessage)}
                <RiArrowDownSFill
                  fontSize={20}
                  style={{
                    marginRight: -5,
                  }}
                />
              </Space>
            </Button>
          </Dropdown>
        </Popconfirm>
      )}
    </Row>
  );
};

export default MemberRow;
