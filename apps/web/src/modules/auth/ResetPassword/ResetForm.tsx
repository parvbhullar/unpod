'use client';
import React from 'react';
import { Button, Divider, Form, Typography } from 'antd';
import { useRouter } from 'next/navigation';
import { AppPassword } from '@unpod/components/antd';
import {
  StyledAuthContainer,
  StyledAuthContent,
  StyledAuthTitle,
} from '../auth.styled';
import AppImage from '@unpod/components/next/AppImage';
import { PASSWORD_REGX } from '@unpod/constants';
import { useIntl } from 'react-intl';

const { Item } = Form;
const { Link, Paragraph } = Typography;

type ResetFormProps = {
  onPasswordReset: (values: {
    password?: string;
    confirm_password?: string;
  }) => void;
};

const ResetForm = ({ onPasswordReset }: ResetFormProps) => {
  const router = useRouter();
  const { formatMessage } = useIntl();

  const onLoginClick = () => {
    router.push('/auth/signin');
  };

  return (
    <StyledAuthContainer>
      <div className="text-center">
        <AppImage
          src={'/images/security.gif'}
          alt="security"
          width={240}
          height={240}
        />

        <StyledAuthTitle $mb={12}>
          {formatMessage({ id: 'auth.setNewPassword' })}
        </StyledAuthTitle>
        <StyledAuthContent type="secondary">
          {formatMessage({ id: 'auth.setNewPasswordDesc' })}
        </StyledAuthContent>
      </div>

      <Form onFinish={onPasswordReset}>
        <Item
          name="password"
          rules={[
            {
              required: true,
              message: formatMessage({ id: 'validation.passwordRequired' }),
            },
            () => ({
              validator(_, value) {
                if (!value) {
                  return Promise.resolve();
                }
                if (!PASSWORD_REGX.test(value)) {
                  return Promise.reject(
                    formatMessage({ id: 'validation.validPassword' }),
                  );
                }
                return Promise.resolve();
              },
            }),
          ]}
        >
          <AppPassword
            placeholder={formatMessage({ id: 'auth.password' })}
            min={8}
          />
        </Item>

        <Item
          name="confirm_password"
          rules={[
            {
              required: true,
              message: formatMessage({ id: 'validation.confirmPassword' }),
            },
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value || getFieldValue('password') === value) {
                  return Promise.resolve();
                }
                return Promise.reject(
                  new Error(
                    formatMessage({ id: 'validation.passwordMismatch' }),
                  ),
                );
              },
            }),
          ]}
        >
          <AppPassword
            placeholder={formatMessage({ id: 'auth.confirmPassword' })}
          />
        </Item>

        <Item>
          <Button type="primary" htmlType="submit" block>
            {formatMessage({ id: 'auth.resetPassword' })}
          </Button>
        </Item>

        <Divider plain>Or</Divider>
        <Paragraph className="text-center">
          <Link onClick={onLoginClick} strong>
            {formatMessage({ id: 'auth.backToLogIn' })}
          </Link>
        </Paragraph>
      </Form>
    </StyledAuthContainer>
  );
};

export default ResetForm;
