'use client';
import React from 'react';
import { useRouter } from 'next/navigation';
import { Button, Divider, Form, Typography } from 'antd';
import AppImage from '@unpod/components/next/AppImage';
import { AppInput } from '@unpod/components/antd';
import { useIntl } from 'react-intl';
import {
  StyledAuthContent,
  StyledAuthTitle,
  StyledHeader,
} from '../auth.styled';

const { Item } = Form;
const { Link, Paragraph } = Typography;

type ForgotPasswordFormProps = {
  onSubmit: (values: { email?: string }) => void;
};

const ForgotPasswordForm = ({ onSubmit }: ForgotPasswordFormProps) => {
  const router = useRouter();
  const { formatMessage } = useIntl();

  const onLoginClick = () => {
    router.push('/auth/signin');
  };

  return (
    <>
      <StyledHeader>
        <AppImage
          src={'/images/security.gif'}
          alt="security"
          width={200}
          height={200}
          style={{ transform: 'scale(1.1)' }}
          priority
        />
        <StyledAuthTitle level={3}>
          {formatMessage({ id: 'auth.forgotPasswordTitle' })}
        </StyledAuthTitle>
        <StyledAuthContent type="secondary">
          {formatMessage({ id: 'auth.forgotPasswordDesc' })}
        </StyledAuthContent>
      </StyledHeader>

      <Form onFinish={onSubmit} size="large">
        <Item
          name="email"
          rules={[
            {
              required: true,
              message: formatMessage({ id: 'validation.enterEmail' }),
            },
          ]}
        >
          <AppInput placeholder={formatMessage({ id: 'form.emailAddress' })} />
        </Item>

        <Item>
          <Button type="primary" htmlType="submit" block size="large">
            {formatMessage({ id: 'auth.sendResetLink' })}
          </Button>
        </Item>
        <Divider plain>{formatMessage({ id: 'auth.or' })}</Divider>
        <Paragraph className="text-center">
          <Link onClick={onLoginClick} strong>
            {formatMessage({ id: 'auth.backToLogin' })}
          </Link>
        </Paragraph>
      </Form>
    </>
  );
};

export default ForgotPasswordForm;
