'use client';
import React from 'react';
import { Button } from 'antd';
import { useRouter } from 'next/navigation';
import AppImage from '@unpod/components/next/AppImage';
import { StyledAuthContent, StyledAuthTitle } from '../auth.styled';
import { useIntl } from 'react-intl';

const ResetLinkSent = () => {
  const router = useRouter();
  const { formatMessage } = useIntl();

  const onContinueCLick = async () => {
    await router.push('/auth/signin');
  };

  return (
    <>
      <div className="text-center">
        <AppImage
          src={'/images/security.gif'}
          alt="verified"
          width={240}
          height={240}
        />

        <StyledAuthTitle $mb={12}>
          {formatMessage({ id: 'auth.forgetPasswordTitle' })}
        </StyledAuthTitle>
        <StyledAuthContent type="secondary">
          {formatMessage({ id: 'auth.forgetPasswordDesc' })}
        </StyledAuthContent>
      </div>

      <Button type="primary" onClick={onContinueCLick} block>
        {formatMessage({ id: 'common.continue' })}
      </Button>
    </>
  );
};

export default React.memo(ResetLinkSent);
