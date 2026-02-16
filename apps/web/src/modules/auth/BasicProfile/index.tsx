'use client';

import React from 'react';
import { Button, Form, Select } from 'antd';
import { AppInput } from '@unpod/components/antd';
import {
  putDataApi,
  useAuthActionsContext,
  useAuthContext,
  useInfoViewActionsContext,
} from '@unpod/providers';
import { useRouter } from 'next/navigation';
import { useIntl } from 'react-intl';
import {
  StyledAuthContainer,
  StyledAuthTitle,
  StyledHeader,
} from '../auth.styled';
import type { User } from '@unpod/constants/types';

const { Item } = Form;

type ProfileRole = {
  role_code?: string;
  role_name?: string;
};

const BasicProfile = () => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const { updateAuthUser } = useAuthActionsContext();
  const { user, globalData } = useAuthContext();
  const router = useRouter();
  const [form] = Form.useForm();
  const { formatMessage } = useIntl();
  const profile_roles =
    (globalData as { profile_roles?: ProfileRole[] }).profile_roles || [];

  const onFinish = (values: {
    first_name: string;
    last_name: string;
    role_name: string;
  }) => {
    putDataApi<User>('user-profile/', infoViewActionsContext, values)
      .then((response) => {
        const res = response as { message?: string; data?: User };
        infoViewActionsContext.showMessage(
          res.message || 'Profile saved',
        );
        updateAuthUser({ ...user, ...(res.data || {}) });

        if (user?.is_private_domain) {
          router.push('/creating-identity/');
        } else {
          router.push('/business-identity/');
        }
      })
      .catch((response: { message?: string }) => {
        infoViewActionsContext.showError(response.message || 'Error');
      });
  };

  return (
    <StyledAuthContainer>
      <StyledHeader>
        <StyledAuthTitle level={3}>
          {formatMessage({ id: 'common.completeProfile' }, { defaultMessage: 'Complete Your Profile' })}
        </StyledAuthTitle>
      </StyledHeader>

      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        initialValues={{
          first_name: user?.first_name || '',
          last_name: user?.last_name || '',
          role_name: '',
        }}
      >
        <Item
          name="first_name"
          rules={[{ required: true, message: 'First name is required' }]}
        >
          <AppInput placeholder={formatMessage({ id: 'common.firstName' }, { defaultMessage: 'First Name' })} />
        </Item>

        <Item
          name="last_name"
          rules={[{ required: true, message: 'Last name is required' }]}
        >
          <AppInput placeholder={formatMessage({ id: 'common.lastName' }, { defaultMessage: 'Last Name' })} />
        </Item>

        {profile_roles.length > 0 && (
          <Item
            name="role_name"
            rules={[{ required: true, message: 'Role is required' }]}
          >
            <Select
              placeholder={formatMessage({ id: 'form.role' }, { defaultMessage: 'Select Role' })}
              size="large"
            >
              {profile_roles.map((role) => (
                <Select.Option key={role.role_code} value={role.role_code}>
                  {role.role_name}
                </Select.Option>
              ))}
            </Select>
          </Item>
        )}

        <Item>
          <Button type="primary" htmlType="submit" block size="large">
            {formatMessage({ id: 'common.continue' }, { defaultMessage: 'Continue' })}
          </Button>
        </Item>
      </Form>
    </StyledAuthContainer>
  );
};

export default BasicProfile;
