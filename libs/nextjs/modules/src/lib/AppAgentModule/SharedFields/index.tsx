import type { Dispatch, SetStateAction } from 'react';
import { useState } from 'react';
import { Button, Flex, Select, Space, Typography } from 'antd';
import { AppSelect } from '@unpod/components/antd';
import { useOrgContext } from '@unpod/providers';
import { ACCESS_ROLE } from '@unpod/constants/AppEnums';
import SharedUserList from './SharedUserList';

const { Option } = Select;

type SharedField = {
  email: string;
  role_code: string;
};

type SharedFieldsProps = {
  sharedFields: SharedField[];
  setSharedFields: Dispatch<SetStateAction<SharedField[]>>;
};

const SharedFields = ({ sharedFields, setSharedFields }: SharedFieldsProps) => {
  const [emails, setEmails] = useState<string[]>([]);
  const [selectedRole, setSelectedRole] = useState('viewer');

  const { orgUsers } = useOrgContext();

  const handleAddSharedField = () => {
    if (emails.length) {
      const userList = emails.map((email) => ({
        email,
        role_code: selectedRole,
      }));
      setSharedFields((prevSharedFields) => [...prevSharedFields, ...userList]);
      setEmails([]);
    }
  };

  const handleDeleteField = (index: number) => {
    setSharedFields(sharedFields.filter((_, i) => i !== index));
  };

  const handleRoleChange = (
    value: string | number | object | unknown[] | null,
  ) => {
    setSelectedRole(typeof value === 'string' ? value : 'viewer');
  };

  const handleEmailChange = (
    emailList: string | number | object | unknown[] | null,
  ) => {
    setEmails(Array.isArray(emailList) ? (emailList as string[]) : []);
  };

  return (
    <Flex vertical gap={24}>
      <Flex gap={24}>
        <AppSelect
          placeholder="Enter Emails"
          mode="tags"
          filterOption={(input: string, option?: any) =>
            String(option?.label ?? '')
              .toLowerCase()
              .includes(input.toLowerCase())
          }
          optionLabelProp="value"
          allowClear
          value={emails}
          onChange={handleEmailChange}
        >
          {orgUsers.map((orgUser, index) => (
            <Option
              key={index}
              value={orgUser.user_email}
              label={`${orgUser.full_name} ${orgUser.user_email}`}
            >
              <Space>
                <Space orientation="vertical" size={0}>
                  {orgUser?.full_name && (
                    <Typography.Text
                      type={'secondary'}
                      style={{ marginBottom: -4, display: 'block' }}
                    >
                      {orgUser?.full_name}
                    </Typography.Text>
                  )}
                  <Typography.Text type={'secondary'}>
                    {orgUser.user_email}
                  </Typography.Text>
                </Space>
              </Space>
            </Option>
          ))}
        </AppSelect>
        <AppSelect
          placeholder="Select Role"
          value={selectedRole}
          onChange={handleRoleChange}
        >
          <Option value={ACCESS_ROLE.VIEWER}>Viewer</Option>
          <Option value={ACCESS_ROLE.EDITOR}>Editor</Option>
        </AppSelect>
        <Button onClick={handleAddSharedField}>Add Emails</Button>
      </Flex>

      <SharedUserList
        sharedFields={sharedFields}
        handleDeleteField={handleDeleteField}
      />
    </Flex>
  );
};

export default SharedFields;
