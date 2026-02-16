import { useRouter } from 'next/navigation';
import type { FC } from 'react';
import { memo } from 'react';
import { useIntl } from 'react-intl';
import {
  StyledAuthContainer,
  StyledAuthContent,
  StyledAuthTitle,
  StyledHeader,
} from '../auth.styled';
import AppImage from '@unpod/components/next/AppImage';
import { Alert, Card, Divider, Space, Typography } from 'antd';

import AppPageLayout from '@unpod/components/common/AppPageLayout';

type VerifyEmailProps = {
  email?: string;
};

const VerifyEmail: FC<VerifyEmailProps> = ({ email }) => {
  const { formatMessage } = useIntl();
  const router = useRouter();

  const onLoginClick = async () => {
    await router.push('/auth/signin');
  };

  return (
    <AppPageLayout layout="full">
      <StyledAuthContainer>
        <Card>
          <StyledHeader>
            <AppImage
              src={'/images/verify-email.webp'}
              alt="Verify email"
              width={240}
              height={240}
              priority
            />

            <StyledAuthTitle level={3} $mb={12}>
              {formatMessage({ id: 'auth.verifyEmail' })}
            </StyledAuthTitle>
            <StyledAuthContent type="secondary">
              {formatMessage({ id: 'auth.sentVerificationLink' })} <br />
              <Typography.Link
                href={`mailto:${email}`}
                strong
                style={{ fontSize: 18 }}
              >
                {email}
              </Typography.Link>
            </StyledAuthContent>
          </StyledHeader>

          <Space orientation="vertical" size="large">
            <Alert
              message={formatMessage({ id: 'auth.checkInbox' })}
              description={formatMessage({ id: 'auth.checkInboxDesc' })}
              type="info"
              showIcon
            />

            <Space
              direction="vertical"
              className="text-center"
              style={{ width: '100%' }}
            >
              <Divider plain>{formatMessage({ id: 'auth.or' })}</Divider>

              <Typography.Link onClick={onLoginClick} strong>
                {formatMessage({ id: 'auth.backToLogin' })}
              </Typography.Link>
            </Space>
          </Space>
        </Card>
      </StyledAuthContainer>
    </AppPageLayout>
  );
};

export default memo(VerifyEmail);
