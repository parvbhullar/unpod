'use client';

import React from 'react';
import { Button } from 'antd';
import { useRouter } from 'next/navigation';
import AppImage from '@unpod/components/next/AppImage';
import {
  StyledAuthContainer,
  StyledAuthContent,
  StyledAuthTitle,
} from '../auth.styled';
import { useIntl } from 'react-intl';

const PasswordChanged = () => {
  const router = useRouter();
  const { formatMessage } = useIntl();

  const onContinueCLick = async () => {
    await router.push('/auth/signin');
  };

  return (
    <StyledAuthContainer>
      <div className="text-center">
        <AppImage
          src={'/images/verified.gif'}
          alt="verified"
          width={240}
          height={240}
        />

        <StyledAuthTitle $mb={12}>
          {formatMessage({ id: 'auth.passwordResetTitle' })}
        </StyledAuthTitle>

        <StyledAuthContent type="secondary">
          {formatMessage({ id: 'auth.passwordResetDescription' })}
        </StyledAuthContent>
      </div>

      <Button type="primary" onClick={onContinueCLick} block>
        {formatMessage({ id: 'common.continue' })}
      </Button>
    </StyledAuthContainer>
  );
};

export default React.memo(PasswordChanged);
