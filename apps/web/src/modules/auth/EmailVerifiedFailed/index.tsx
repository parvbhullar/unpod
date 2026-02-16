'use client';
import React from 'react';
import { useRouter } from 'next/navigation';
import AppPageLayout from '@unpod/components/common/AppPageLayout';
import {
  StyledAuthContainer,
  StyledAuthContent,
  StyledAuthTitle,
  StyledAvatar,
} from '../auth.styled';
import { Button, Card } from 'antd';
import { MdClose } from 'react-icons/md';
import { useIntl } from 'react-intl';

const EmailVerifiedFailed = () => {
  const router = useRouter();
  const { formatMessage } = useIntl();

  const onContinueCLick = async () => {
    await router.push('/');
  };

  return (
    <AppPageLayout layout="full">
      <StyledAuthContainer>
        <Card>
          <div className="text-center">
            <StyledAvatar
              size={160}
              style={{ lineHeight: '1.8' }}
              icon={<MdClose fontSize={80} />}
            />

            <StyledAuthTitle $mb={12}>
              {formatMessage({ id: 'auth.emailVerificationFailed' })}
            </StyledAuthTitle>

            <StyledAuthContent type="danger">
              {formatMessage({ id: 'auth.invalidOrExpiredLink' })}
            </StyledAuthContent>
          </div>

          <Button type="primary" onClick={onContinueCLick} block>
            {formatMessage({ id: 'common.goToHome' })}
          </Button>
        </Card>
      </StyledAuthContainer>
    </AppPageLayout>
  );
};

export default EmailVerifiedFailed;
