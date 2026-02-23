'use client';

import {useState} from 'react';
import {Button, Select, Space, Typography} from 'antd';
import type {DefaultOptionType} from 'antd/es/select';
import {useIntl} from 'react-intl';

import {StyledFormContainer} from './index.styled';
import type {GlobalRoleMap, InviteUserSectionProps, PermissionEntity, PermissionMember,} from './types';

import AppSelect from '../../antd/AppSelect';
import UserAvatar from '../UserAvatar';

import {ACCESS_ROLE} from '@unpod/constants/AppEnums';
import {EMAIL_REGX} from '@unpod/constants';
import {postDataApi, useAuthContext, useInfoViewActionsContext,} from '@unpod/providers';
import {getSpaceAllowedRoles} from '@unpod/helpers/PermissionHelper';
import {maskEmail} from '@unpod/helpers/StringHelper';
import {getRoleLabel} from '@unpod/helpers/LocalizationFormatHelper';

const getInviteUserUrl = (
  type: InviteUserSectionProps['type'],
  currentData?: PermissionEntity | null,
): string => {
  switch (type) {
    case 'org':
      return `organization/${currentData?.domain_handle || ''}/invite/`;
    case 'space':
      return `spaces/${currentData?.token || ''}/invite/`;
    default:
      return `threads/${currentData?.slug || ''}/permission/`;
  }
};

const getPopupContainer = (triggerNode: HTMLElement): HTMLElement => {
  return triggerNode.parentElement ?? triggerNode;
};

const InviteUserSection = ({
                             type,
                             userList,
                             setUserList,
                             currentData,
                             setCurrentData,
                           }: InviteUserSectionProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const {user, globalData} = useAuthContext();
  const {formatMessage} = useIntl();

  const [emails, setEmails] = useState<string[]>([]);
  const [selectedRole, setSelectedRole] = useState<string>(ACCESS_ROLE.VIEWER);

  const roles = (globalData.roles as GlobalRoleMap) || {};

  const onAddClick = (): void => {
    if (emails.length === 0) return;

    const newUsers = emails.map((email) => ({
      email,
      role_code: selectedRole,
    }));

    const url = getInviteUserUrl(type, currentData);

    postDataApi<{ success_data?: PermissionMember[] }>(
      url,
      infoViewActionsContext,
      newUsers,
    )
      .then((response) => {
        infoViewActionsContext.showMessage(response.message || 'Updated');

        const successfulUsers = response.data?.success_data || [];
        const users = [...userList, ...successfulUsers];

        setUserList(users);
        setCurrentData({
          ...(currentData || {}),
          users,
        });

        setEmails([]);
        setSelectedRole(ACCESS_ROLE.VIEWER);
      })
      .catch((error: unknown) => {
        const message =
          error && typeof error === 'object' && 'message' in error
            ? String((error as { message?: string }).message || '')
            : 'Something went wrong';
        infoViewActionsContext.showError(message);
      });
  };

  const onEmailChange = (
    newEmails: string | number | object | unknown[] | null,
  ): void => {
    if (!Array.isArray(newEmails)) {
      setEmails([]);
      return;
    }

    const validEmails = newEmails
      .filter((email): email is string => typeof email === 'string')
      .filter((email) => EMAIL_REGX.test(email));

    setEmails(validEmails);
  };

  const onRoleChange = (
    value: string | number | object | unknown[] | null,
  ): void => {
    if (typeof value === 'string') {
      setSelectedRole(value);
    }
  };

  const roleData = type === 'space' ? roles.space || [] : roles.post || [];

  return (
    <StyledFormContainer>
      {currentData?.slug ? (
        <AppSelect
          mode="tags"
          placeholder={formatMessage({id: 'invite.enterEmails'})}
          style={{flex: 1}}
          value={emails}
          onChange={onEmailChange}
          allowClear
          optionLabelProp="value"
          filterOption={(input: string, option?: DefaultOptionType) =>
            String(option?.label || '')
              .toLowerCase()
              .includes(input.toLowerCase())
          }
          getPopupContainer={getPopupContainer}
        >
          {userList.map((orgUser, index) => {
            const userEmail = orgUser.email || orgUser.user_email || '';
            const fullName = orgUser.full_name || '';
            return (
              <Select.Option
                key={userEmail || index}
                value={userEmail}
                label={`${fullName} ${userEmail}`.trim()}
              >
                <Space>
                  <UserAvatar user={orgUser}/>
                  <Space orientation="vertical" size={0}>
                    {fullName ? (
                      <Typography.Text
                        type="secondary"
                        style={{marginBottom: -4, display: 'block'}}
                      >
                        {fullName}
                      </Typography.Text>
                    ) : null}
                    <Typography.Text type="secondary">
                      {maskEmail(userEmail)}
                    </Typography.Text>
                  </Space>
                </Space>
              </Select.Option>
            );
          })}
        </AppSelect>
      ) : (
        <AppSelect
          mode="tags"
          placeholder={formatMessage({id: 'invite.enterEmails'})}
          style={{flex: 1}}
          value={emails}
          onChange={onEmailChange}
          getPopupContainer={getPopupContainer}
        />
      )}

      <AppSelect
        placeholder={formatMessage({id: 'invite.role'})}
        value={selectedRole}
        onChange={onRoleChange}
        style={{width: 100}}
        getPopupContainer={getPopupContainer}
        dropdownMatchSelectWidth={false}
        dropdownStyle={{flex: 1}}
      >
        {getSpaceAllowedRoles(roleData, userList, user).map((role, index) => {
          const roleCode = role.role_code || ACCESS_ROLE.VIEWER;
          if (roleCode === ACCESS_ROLE.OWNER) return null;

          return (
            <Select.Option key={`${roleCode}-${index}`} value={roleCode}>
              {getRoleLabel(roleCode, formatMessage)}
            </Select.Option>
          );
        })}
      </AppSelect>

      <Button
        type="primary"
        onClick={onAddClick}
        disabled={!selectedRole || emails.length === 0}
      >
        {formatMessage({id: 'common.add'})}
      </Button>
    </StyledFormContainer>
  );
};

export default InviteUserSection;
