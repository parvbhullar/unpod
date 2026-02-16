'use client';
import React, { useEffect, useState } from 'react';
import { Button, Col, Form, Row, Select, Upload, type UploadProps } from 'antd';
import {
  AppGridContainer,
  AppInput,
  AppSelect,
  AppTextArea,
} from '@unpod/components/antd';
import { StyledFlex, StyledRoot } from './index.styled';
import {
  putDataApi,
  uploadPutDataApi,
  useAuthActionsContext,
  useAuthContext,
  useInfoViewActionsContext,
} from '@unpod/providers';
import styled from 'styled-components';
import { useIntl } from 'react-intl';
import type { User } from '@unpod/constants/types';

const { Item } = Form;

export const UserUploadImg = styled.img`
  width: 150px;
  height: 150px;
  object-fit: cover;
`;

type ProfileRole = {
  role_code?: string;
  role_name?: string;
};

type EditProfileProps = {
  user: User;
};

const EditProfile: React.FC<EditProfileProps> = ({ user }) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const { updateAuthUser } = useAuthActionsContext();
  const [form] = Form.useForm();
  const { globalData } = useAuthContext();
  const profile_roles =
    (globalData as { profile_roles?: ProfileRole[] }).profile_roles || [];
  const [userAvatar, setUserAvatar] = useState<string>(() => {
    const avatar = user?.user_detail?.profile_picture;
    return typeof avatar === 'string' ? avatar : '';
  });
  const { formatMessage } = useIntl();

  useEffect(() => {
    if (user)
      form.setFieldsValue({
        first_name: user.first_name,
        last_name: user.last_name,
        email: user.email,
        role_name: user.user_detail?.role_name,
        description: user.user_detail?.description || '',
      });
  }, [user]);

  const onSubmitSuccess = (formData: Record<string, unknown>) => {
    putDataApi<unknown>('user-profile/', infoViewActionsContext, formData)
      .then((response) => {
        const res = response as { message?: string; data?: User };
        infoViewActionsContext.showMessage(res.message || 'Saved');
        updateAuthUser({ ...user, ...(res.data || {}) });
      })
      .catch((response) => {
        const res = response as { message?: string };
        infoViewActionsContext.showError(res.message || 'Error');
      });
  };

  const handleUploadChange: NonNullable<UploadProps['beforeUpload']> = (
    info,
  ) => {
    const formData = new FormData();
    formData.append('profile_picture', info);
    uploadPutDataApi<any>(`user-profile/`, infoViewActionsContext, formData)
      .then((data) => {
        const res = data;
        infoViewActionsContext.showMessage(res.message || 'Updated');
        updateAuthUser({ ...user, ...(res.data || {}) });
        const nextAvatar = res.data?.user_detail?.profile_picture;
        setUserAvatar(typeof nextAvatar === 'string' ? nextAvatar : '');
      })
      .catch((error) => {
        const err = error as { message?: string };
        infoViewActionsContext.showError(err.message || 'Error');
      });
    return false;
  };
  return (
    <StyledRoot>
      <Form form={form} onFinish={onSubmitSuccess}>
        <StyledFlex align={'flex-start'} gap={24}>
          <AppGridContainer gutter={[24, 24]}>
            <Col sm={24} md={12}>
              <Item
                name="first_name"
                rules={[
                  {
                    required: true,
                    message: formatMessage({ id: 'validation.enterFirstName' }),
                  },
                ]}
              >
                <AppInput
                  placeholder={formatMessage({ id: 'form.firstName' })}
                />
              </Item>
            </Col>

            <Col sm={24} md={12}>
              <Item
                name="last_name"
                rules={[
                  {
                    required: true,
                    message: formatMessage({ id: 'validation.enterLastName' }),
                  },
                ]}
              >
                <AppInput
                  placeholder={formatMessage({ id: 'form.lastName' })}
                />
              </Item>
            </Col>
            <Col sm={24} md={12}>
              <Item
                name="email"
                rules={[
                  {
                    required: true,
                    message: formatMessage({ id: 'validation.enterEmail' }),
                  },
                ]}
              >
                <AppInput
                  placeholder={formatMessage({ id: 'form.email' })}
                  disabled
                />
              </Item>
            </Col>

            <Col sm={24} md={12}>
              <Item
                name="role_name"
                rules={[
                  {
                    required: true,
                    message: formatMessage({ id: 'validation.selectRole' }),
                  },
                ]}
              >
                <AppSelect
                  placeholder={formatMessage({ id: 'form.role' })}
                  asterisk
                >
                  {profile_roles.map((role) => (
                    <Select.Option key={role.role_code} value={role.role_code}>
                      {role.role_name}
                    </Select.Option>
                  ))}
                </AppSelect>
              </Item>
            </Col>

            <Col sm={24}>
              <Item name="description">
                <AppTextArea
                  placeholder={formatMessage({ id: 'form.description' })}
                  maxLength={250}
                  rows={4}
                />
              </Item>
            </Col>
          </AppGridContainer>

          <Col sm={24} md={8}>
            <Upload
              accept=".png, .jpg,.jpeg"
              showUploadList={false}
              beforeUpload={handleUploadChange}
              maxCount={1}
            >
              <UserUploadImg
                src={userAvatar ? userAvatar : '/images/placeholder.png'}
                alt="logo"
              />
            </Upload>
          </Col>
        </StyledFlex>
        <Row>
          <Button type="primary" htmlType="submit">
            {formatMessage({ id: 'common.saveProfile' })}
          </Button>
        </Row>
      </Form>
    </StyledRoot>
  );
};

export default EditProfile;
