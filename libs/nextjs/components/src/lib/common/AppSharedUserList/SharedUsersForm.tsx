import React, {useMemo, useState} from 'react';
import {Button, Flex, Select, Space, Typography} from 'antd';
import {AppSelect} from '../../antd';
import {useOrgContext} from '@unpod/providers';
import UserAvatar from '../../common/UserAvatar';
import {useIntl} from 'react-intl';
import type {DefaultOptionType} from 'antd/es/select';
import type {InviteMember} from '@unpod/constants/types';

type RoleOption = {
  key: string;
  label: string;
};

type User = {
  email: string;
  role_code: string;
};

type SharedUsersFormProps = {
  onAddUsers?: (users: User[]) => void;
  allowedRoles?: RoleOption[];
  defaultRole?: string;
  selectedUsers?: InviteMember[];
};

const SharedUsersForm: React.FC<SharedUsersFormProps> = ({
                                                           onAddUsers,
                                                           allowedRoles,
                                                           defaultRole = 'viewer',
                                                           selectedUsers,
                                                         }) => {
  const [userEmails, setUserEmails] = useState<string[]>([]);
  const [role, setRole] = useState(defaultRole);
  const {orgUsers} = useOrgContext();
  const {formatMessage} = useIntl();
  const roleOptions = allowedRoles ?? [];

  const handleAddUsers = () => {
    if (userEmails.length === 0) {
      return;
    }
    const users = userEmails.map((email) => ({
      email,
      role_code: role,
    }));
    setUserEmails([]);
    onAddUsers?.(users);
  };

  const selectedEmails = useMemo(() => {
    return (selectedUsers || []).map((item) => item.email);
  }, [selectedUsers]);

  return (
    <Flex align="vertical" gap={12}>
      <AppSelect
        placeholder={formatMessage({id: 'common.selectUsers'})}
        mode="tags"
        filterOption={(input: string, option?: DefaultOptionType) =>
          String(option?.label ?? '')
            .toLowerCase()
            .includes(input.toLowerCase())
        }
        optionLabelProp="value"
        value={selectedEmails}
        onChange={(emails: string | number | object | unknown[] | null) =>
          setUserEmails(Array.isArray(emails) ? (emails as string[]) : [])
        }
        allowClear
      >
        {orgUsers.map((orgUser, index) => (
          <Select.Option
            key={index}
            value={orgUser.user_email}
            label={`${orgUser.full_name} ${orgUser.user_email}`}
          >
            <Space>
              <UserAvatar user={orgUser}/>
              <Space orientation="vertical" size={0}>
                {orgUser?.full_name && (
                  <Typography.Text
                    type={'secondary'}
                    style={{marginBottom: -4, display: 'block'}}
                  >
                    {orgUser?.full_name}
                  </Typography.Text>
                )}
                <Typography.Text type={'secondary'}>
                  {orgUser.user_email}
                </Typography.Text>
              </Space>
            </Space>
          </Select.Option>
        ))}
      </AppSelect>
      {roleOptions.length > 0 && (
        <AppSelect
          placeholder={formatMessage({id: 'common.selectRole'})}
          value={role}
          onChange={(value: string | number | object | unknown[] | null) =>
            setRole(typeof value === 'string' ? value : defaultRole)
          }
        >
          {roleOptions.map((item, index) => (
            <Select.Option key={index} value={item.key}>
              {formatMessage({id: item.label})}
            </Select.Option>
          ))}
        </AppSelect>
      )}
      <Button
        type="primary"
        disabled={!role || userEmails.length === 0}
        onClick={handleAddUsers}
      >
        {formatMessage({id: 'common.add'})}
      </Button>
    </Flex>
  );
};

export default SharedUsersForm;
